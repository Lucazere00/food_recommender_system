import os
import sys
import re
import pandas as pd
import numpy as np
import scipy.sparse as sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ast

# NLTK per la normalizzazione e lo stemming
import nltk
from nltk.stem import PorterStemmer

# Scarichiamo le risorse minime necessarie se non presenti
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class ContentBasedRecommender:
    def __init__(self, matrix_path="dataset/tfidf_matrix.npz"):
        """
        Inizializza il motore Content-Based (Svuota-Frigo).
        """
        self.matrix_path = matrix_path
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = None
        self.df_recipes = None
        self.stemmer = PorterStemmer()
        
        # Parole comuni da rimuovere (stop-words culinarie)
        self.stop_words_culinary = {
            'fresh', 'large', 'small', 'chopped', 'diced', 'sliced', 'minced', 
            'ground', 'shredded', 'drain', 'dried', 'frozen', 'skinless', 'boneless',
            'halves', 'pieces', 'cloves', 'teaspoon', 'tablespoon', 'cup', 'lbs', 'oz'
        }

    def _clean_and_stem_ingredients(self, ingredients_list):
        """
        Normalizza la lista di ingredienti: lowercase, rimozione numeri/misure,
        rimozione stop-words culinarie e applicazione dello Stemming.
        """
        cleaned_words = []
        for ing in ingredients_list:
            # 1. Lowercase e rimozione caratteri speciali/numeri
            ing = ing.lower()
            ing = re.sub(f'[^a-zA-Z\s]', '', ing)
            
            # 2. Tokenizzazione in singole parole
            words = ing.split()
            
            for word in words:
                # 3. Rimozione stop-words culinarie
                if word not in self.stop_words_culinary:
                    # 4. Stemming (es. breasts -> breast, potatoes -> potato)
                    stemmed_word = self.stemmer.stem(word)
                    cleaned_words.append(stemmed_word)
                    
        return " ".join(cleaned_words)

    def fit(self, df_recipes, force_recalculate=False):
        """
        FASE OFFLINE: Costruisce o carica la matrice TF-IDF degli ingredienti.
        """
        self.df_recipes = df_recipes.copy()
        
        # Assicuriamoci che la colonna ingredients sia una vera lista Python
        if isinstance(self.df_recipes['ingredients'].iloc[0], str):
            self.df_recipes['ingredients'] = self.df_recipes['ingredients'].apply(lambda x: ast.literal_eval(x))

        # Se la matrice esiste già su disco e non forziamo il ricalcolo, la carichiamo al volo
        if os.path.exists(self.matrix_path) and not force_recalculate:
            print(f"-> Caricamento matrice TF-IDF pre-calcolata da {self.matrix_path}...")
            self.tfidf_matrix = sparse.load_npz(self.matrix_path)
            # Dobbiamo fittare il vectorizer sulle stringhe per ripristinare il vocabolario
            corpus = self.df_recipes['ingredients'].apply(self._clean_and_stem_ingredients)
            self.vectorizer.fit(corpus)
        else:
            print("-> Generazione matrice TF-IDF (Fase Offline)...")
            # 1. Pre-elaborazione di tutte le ricette
            corpus = self.df_recipes['ingredients'].apply(self._clean_and_stem_ingredients)
            
            # 2. Fit & Transform del TF-IDF Vectorizer
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
            
            # 3. Salvataggio su disco in formato compresso .npz
            os.makedirs(os.path.dirname(self.matrix_path), exist_ok=True)
            sparse.save_npz(self.matrix_path, self.tfidf_matrix)
            print(f"-> Matrice TF-IDF salvata con successo in: {self.matrix_path}")

    def recommend(self, user_ingredients, max_missing_ingredients=2, top_k=10):
        """
        FASE ONLINE: Calcola la similarità in tempo reale basandosi sugli ingredienti inseriti.
        """
        if self.tfidf_matrix is None:
            raise ValueError("Il modello non è strutturato. Esegui il metodo .fit() prima.")

        # 1. Pulizia e stemming della query dell'utente
        query_string = self._clean_and_stem_ingredients(user_ingredients)
        
        if not query_string.strip():
            return [] # Se l'utente non inserisce ingredienti validi
            
        # 2. Trasformazione della query nel vettore TF-IDF (SOLO transform!)
        query_vector = self.vectorizer.transform([query_string])
        
        # 3. Calcolo della Cosine Similarity tra la query e TUTTE le ricette
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Creiamo un set degli ingredienti inseriti (normalizzati/stemmati) per fare i conteggi di match
        user_stems = set(query_string.split())
        
        results = []
        
        # Per ottimizzare le performance, analizziamo solo le ricette che hanno almeno un briciolo di similarità
        matched_indices = np.where(similarities > 0.0)[0]
        
        for idx in matched_indices:
            row = self.df_recipes.iloc[idx]
            sim_score = similarities[idx]
            
            # Recuperiamo gli ingredienti originali della ricetta
            recipe_ingredients = row['ingredients']
            
            # Calcoliamo quali ingredienti l'utente possiede e quali mancano
            found = []
            missing = []
            
            for ing in recipe_ingredients:
                # Applichiamo lo stesso stemming per fare il confronto equo
                ing_stemmed = self._clean_and_stem_ingredients([ing])
                ing_words = set(ing_stemmed.split())
                
                # Se c'è intersezione tra le parole dell'ingrediente e quelle della query, è un match
                if ing_words and ing_words.issubset(user_stems):
                    found.append(ing)
                else:
                    missing.append(ing)
            
            # Applichiamo il vincolo richiesto: controllo degli ingredienti mancanti massimi
            if len(missing) <= max_missing_ingredients:
                results.append({
                    'id': int(row['id']),
                    'name': row['name'],
                    'similarity': round(float(sim_score), 4),
                    'ingredienti_trovati': found,
                    'ingredienti_mancanti': missing,
                    'minuti': int(row['minutes']),
                    'calorie': round(float(row['calories']), 1)
                })
                
        # Ordiniamo i risultati finali per similarità decrescente
        results = sorted(results, key=lambda x: x['similarity'], reverse=True)
        
        return results[:top_k]