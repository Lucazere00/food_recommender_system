import os
import sys
import re
import pandas as pd
import numpy as np
import scipy.sparse as sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ast

import nltk
from nltk.stem import PorterStemmer

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import PATH_CLEAN_RECIPES, PATH_TFIDF_MATRIX


def ensure_list_column(series):
    if series.empty:
        return series
    first_valid = series.dropna().iloc[0] if not series.dropna().empty else None
    if first_valid is None or isinstance(first_valid, list):
        return series
    return series.apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else [])


class ContentBasedRecommender:
    def __init__(self, matrix_path=PATH_TFIDF_MATRIX):
        self.matrix_path = matrix_path
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = None
        self.df_recipes = None
        self.stemmer = PorterStemmer()

        self.stop_words_culinary = {
            'fresh', 'large', 'small', 'chopped', 'diced', 'sliced', 'minced',
            'ground', 'shredded', 'drain', 'dried', 'frozen', 'skinless', 'boneless',
            'halves', 'pieces', 'cloves', 'teaspoon', 'tablespoon', 'cup', 'lbs', 'oz'
        }

    def _clean_and_stem_ingredients(self, ingredients_list):
        cleaned_words = []
        for ing in ingredients_list:
            ing = ing.lower()
            ing = re.sub(r'[^a-zA-Z\s]', '', ing)
            words = ing.split()
            for word in words:
                if word not in self.stop_words_culinary:
                    stemmed_word = self.stemmer.stem(word)
                    cleaned_words.append(stemmed_word)
        return " ".join(cleaned_words)

    def fit(self, df_recipes, force_recalculate=False):
        """
        FASE OFFLINE: costruisce o carica la matrice TF-IDF degli ingredienti.
        """
        self.df_recipes = df_recipes.copy()
        self.df_recipes['ingredients'] = ensure_list_column(self.df_recipes['ingredients'])

        if os.path.exists(self.matrix_path) and not force_recalculate:
            print(f"-> Caricamento matrice TF-IDF pre-calcolata da {self.matrix_path}...")
            self.tfidf_matrix = sparse.load_npz(self.matrix_path)
            corpus = self.df_recipes['ingredients'].apply(self._clean_and_stem_ingredients)
            self.vectorizer.fit(corpus)
        else:
            print("-> Generazione matrice TF-IDF (Fase Offline)...")
            corpus = self.df_recipes['ingredients'].apply(self._clean_and_stem_ingredients)
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

            dir_path = os.path.dirname(self.matrix_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            sparse.save_npz(self.matrix_path, self.tfidf_matrix)
            print(f"-> Matrice TF-IDF salvata in: {self.matrix_path}")

    def _count_missing(self, row, user_ingredient_stems):
        """Calcola ingredienti trovati e mancanti per una ricetta."""
        found = []
        missing = []
        for ing in row['ingredients']:
            ing_stemmed = self._clean_and_stem_ingredients([ing])
            ing_words = set(ing_stemmed.split())
            if ing_words and any(
                ing_words.issubset(user_stems)
                for user_stems in user_ingredient_stems
            ):
                found.append(ing)
            else:
                missing.append(ing)
        return found, missing

    def recommend(self, user_ingredients, max_missing_ingredients=2, top_k=10):
        """
        FASE ONLINE: calcola la similarita in tempo reale sugli ingredienti inseriti.
        """
        if self.tfidf_matrix is None:
            raise ValueError("Il modello non e strutturato. Esegui .fit() prima.")

        query_string = self._clean_and_stem_ingredients(user_ingredients)

        if not query_string.strip():
            return []

        query_vector = self.vectorizer.transform([query_string])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        user_ingredient_stems = [
            set(self._clean_and_stem_ingredients([ingredient]).split())
            for ingredient in user_ingredients
        ]
        user_ingredient_stems = [
            stems for stems in user_ingredient_stems if stems
        ]
        matched_indices = np.where(similarities > 0.0)[0]

        # Vettorizzato: estrae il sottoinsieme di ricette con similarita > 0
        matched_df = self.df_recipes.iloc[matched_indices].copy()
        matched_df['similarity'] = similarities[matched_indices]
        matched_df = matched_df.sort_values('similarity', ascending=False)

        results = []
        for _, row in matched_df.iterrows():
            found, missing = self._count_missing(row, user_ingredient_stems)
            if len(missing) <= max_missing_ingredients:
                results.append({
                    'id':                    int(row['id']),
                    'name':                  row['name'],
                    'similarity':            round(float(row['similarity']), 4),
                    'ingredienti_trovati':   found,
                    'ingredienti_mancanti':  missing,
                    'minuti':                int(row['minutes']),
                    'calorie':               round(float(row['calories']), 1)
                })
            if len(results) == top_k:
                break

        return results
