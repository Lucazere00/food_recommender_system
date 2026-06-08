import os
import sys
import pandas as pd
import numpy as np
import ast

# Permette l'importazione dal file config posizionato nella cartella radice
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import PATH_CLEAN_RECIPES

class MoodBasedRecommender:
    def __init__(self):
        self.df_recipes = None
        self.df_mood_vectors = None
        
        # Parole chiave per ingredienti costosi (Dimensione Price)
        self.luxury_ingredients = {'lobster', 'truffle', 'wagyu', 'caviar', 'saffron', 'ribeye', 'shrimp', 'prosciutto'}

    def fit(self, df_recipes):
        """
        FASE OFFLINE: Calcola il vettore a 6 dimensioni per ogni ricetta nel dataset.
        """
        self.df_recipes = df_recipes.copy()
        
        # Assicuriamoci che tags e ingredients siano liste vere
        if isinstance(self.df_recipes['tags'].iloc[0], str):
            self.df_recipes['tags'] = self.df_recipes['tags'].apply(lambda x: ast.literal_eval(x))
        if isinstance(self.df_recipes['ingredients'].iloc[0], str):
            self.df_recipes['ingredients'] = self.df_recipes['ingredients'].apply(lambda x: ast.literal_eval(x))
            
        print("-> Estrazione automatica delle 6 dimensioni del Mood per ogni ricetta...")
        
        # Inizializziamo le colonne delle 6 dimensioni
        dimensions = ['body', 'time', 'taste', 'price', 'mental', 'modification']
        for d in dimensions:
            self.df_recipes[d] = 0.0
            
        # Applichiamo le regole euristiche riga per riga (vettorizzato o via apply per stabilità)
        self.df_recipes = self.df_recipes.apply(self._compute_recipe_mood, axis=1)
        
        # NORMALIZZAZIONE nel range [-5, +5] per allinearsi perfettamente agli slider dell'utente
        for d in dimensions:
            min_val = self.df_recipes[d].min()
            max_val = self.df_recipes[d].max()
            if max_val != min_val:
                # Mappa prima in [0, 1], poi scala in [-5, +5]
                self.df_recipes[d] = ((self.df_recipes[d] - min_val) / (max_val - min_val)) * 10 - 5
            else:
                self.df_recipes[d] = 0.0
                
        # Salviamo la matrice dei vettori per velocizzare la fase online
        self.df_mood_vectors = self.df_recipes[dimensions].values
        print("-> Matrice Mood generata e normalizzata in scala [-5, +5]!")

    def _compute_recipe_mood(self, row):
        """
        Calcola i punteggi grezzi di una singola ricetta in base a tag, ingredienti e macro.
        """
        tags = set([t.lower().strip() for t in row['tags']])
        ingredients = set([i.lower().strip() for i in row['ingredients']])
        
        # 1. BODY (Mangiare di cuore + / Leggero -)
        if 'comfort-food' in tags or 'hearty' in tags or 'meat' in tags or row['calories'] > 600:
            row['body'] += 2.0
        if 'light' in tags or 'salad' in tags or 'low-calorie' in tags or row['calories'] < 200:
            row['body'] -= 2.0
            
        # 2. TIME (Elaborato + / Veloce -)
        if row['minutes'] > 60 or row['n_steps'] > 10:
            row['time'] += 2.0
        if '15-minutes-or-less' in tags or '30-minutes-or-less' in tags or row['minutes'] <= 20:
            row['time'] -= 2.0
            
        # 3. TASTE (Rico/Intenso + / Delicato -)
        if row['total_fat_pct'] > 30 or row['sugar_pct'] > 30 or 'rich' in tags or 'creamy' in tags or 'cheesy' in tags:
            row['taste'] += 2.0
        if 'light' in tags or 'low-fat' in tags or (row['protein_pct'] > 20 and row['total_fat_pct'] < 10):
            row['taste'] -= 2.0
            
        # 4. PRICE (Costoso + / Economico -)
        if ingredients.intersection(self.luxury_ingredients):
            row['price'] += 3.0  # Peso extra per ingredienti di lusso espliciti
        if 'budget-friendly' in tags or 'cheap' in tags or '5-ingredients-or-less' in tags or len(ingredients) <= 4:
            row['price'] -= 2.0
            
        # 5. MENTAL (Comfort/Sgarro + / Salutare -)
        if 'comfort-food' in tags or 'soul-food' in tags or 'chocolate' in tags or 'desserts' in tags:
            row['mental'] += 2.0
        if 'healthy' in tags or 'low-sodium' in tags or 'diabetic-friendly' in tags:
            row['mental'] -= 2.0
            
        # 6. MODIFICATION (Sperimentale + / Classico -)
        if 'fusion' in tags or 'exotic' in tags or 'ethic' in tags:
            row['modification'] += 2.0
        if 'traditional' in tags or 'classic' in tags or 'old-fashioned' in tags:
            row['modification'] -= 2.0
            
        return row

    def recommend(self, body=0.0, time=0.0, taste=0.0, price=0.0, mental=0.0, modification=0.0, top_k=10):
        """
        FASE ONLINE: Calcola la distanza Euclidea tra il vettore dell'utente e quelli delle ricette.
        """
        if self.df_mood_vectors is None:
            raise ValueError("Il modello non è strutturato. Chiama .fit() prima.")
            
        # Creiamo il vettore dell'utente basato sugli slider (-5 a +5)
        user_vector = np.array([body, time, taste, price, mental, modification], dtype=float)
        
        # Calcoliamo la distanza Euclidea per ogni ricetta
        # Distanza = radice(somma((vettore_utente - vettore_ricetta)^2))
        distances = np.linalg.norm(self.df_mood_vectors - user_vector, axis=1)
        
        # Creiamo una copia del dataframe per inserire i risultati del ranking
        df_result = self.df_recipes.copy()
        df_result['distance'] = distances
        
        # Più la distanza è piccola, più la ricetta rispecchia il mood dell'utente
        df_top = df_result.sort_values(by='distance', ascending=True).head(top_k)
        
        output = []
        for _, row in df_top.iterrows():
            output.append({
                'id': int(row['id']),
                'name': row['name'],
                'distanza_geometrica': round(float(row['distance']), 4),
                'mood_scores': {
                    'body': round(float(row['body']), 2),
                    'time': round(float(row['time']), 2),
                    'taste': round(float(row['taste']), 2),
                    'price': round(float(row['price']), 2),
                    'mental': round(float(row['mental']), 2),
                    'modification': round(float(row['modification']), 2)
                },
                'minuti': int(row['minutes']),
                'calorie': round(float(row['calories']), 1)
            })
            
        return output