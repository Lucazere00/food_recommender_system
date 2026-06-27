import os
import sys
import pandas as pd
import numpy as np
import ast

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import PATH_CLEAN_RECIPES


def ensure_list_column(series):
    if series.empty:
        return series
    first_valid = series.dropna().iloc[0] if not series.dropna().empty else None
    if first_valid is None or isinstance(first_valid, list):
        return series
    return series.apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else [])


class MoodBasedRecommender:
    def __init__(self):
        self.df_recipes = None
        self.df_mood_vectors = None

        self.luxury_ingredients = {
            'lobster', 'truffle', 'wagyu', 'caviar', 'saffron',
            'ribeye', 'shrimp', 'prosciutto'
        }

        # Pesi differenziati per segnale (piu difendibili di un +2.0 fisso)
        self.body_signals    = {'comfort-food': 2.0, 'hearty': 1.5, 'meat': 1.0}
        self.mental_signals  = {'comfort-food': 2.0, 'soul-food': 2.0,
                                'chocolate': 1.5, 'desserts': 1.5}
        self.taste_signals   = {'rich': 2.0, 'creamy': 2.0, 'cheesy': 1.5}
        self.mod_pos_signals = {'fusion': 2.0, 'exotic': 2.0, 'ethic': 1.5}
        self.mod_neg_signals = {'traditional': -2.0, 'classic': -2.0, 'old-fashioned': -1.5}

    def fit(self, df_recipes):
        """FASE OFFLINE: calcola il vettore a 6 dimensioni per ogni ricetta."""
        self.df_recipes = df_recipes.copy()

        self.df_recipes['tags']        = ensure_list_column(self.df_recipes['tags'])
        self.df_recipes['ingredients'] = ensure_list_column(self.df_recipes['ingredients'])

        print("-> Estrazione automatica delle 6 dimensioni del Mood per ogni ricetta...")

        dimensions = ['body', 'time', 'taste', 'price', 'mental', 'modification']
        for d in dimensions:
            self.df_recipes[d] = 0.0

        self.df_recipes = self.df_recipes.apply(self._compute_recipe_mood, axis=1)

        # Normalizzazione in [-5, +5]
        for d in dimensions:
            min_val = self.df_recipes[d].min()
            max_val = self.df_recipes[d].max()
            if max_val != min_val:
                self.df_recipes[d] = ((self.df_recipes[d] - min_val) /
                                      (max_val - min_val)) * 10 - 5
            else:
                self.df_recipes[d] = 0.0

        # Validazione range
        for d in dimensions:
            assert self.df_recipes[d].between(-5.001, 5.001).all(), \
                f"Normalizzazione fallita per dimensione {d}"

        self.df_mood_vectors = self.df_recipes[dimensions].values
        print("-> Matrice Mood generata e normalizzata in scala [-5, +5]!")

    def _compute_recipe_mood(self, row):
        """Calcola i punteggi grezzi di una singola ricetta."""
        tags        = set([t.lower().strip() for t in row['tags']])
        ingredients = set([i.lower().strip() for i in row['ingredients']])

        # 1. BODY
        for tag, weight in self.body_signals.items():
            if tag in tags:
                row['body'] += weight
        if row['calories'] > 600:
            row['body'] += 2.0
        if 'light' in tags or 'salad' in tags or 'low-calorie' in tags \
                or row['calories'] < 200:
            row['body'] -= 2.0

        # 2. TIME
        if row['minutes'] > 60 or row['n_steps'] > 10:
            row['time'] += 2.0
        if '15-minutes-or-less' in tags or '30-minutes-or-less' in tags \
                or row['minutes'] <= 20:
            row['time'] -= 2.0

        # 3. TASTE
        if row['total_fat_pct'] > 30 or row['sugar_pct'] > 30:
            row['taste'] += 1.5
        for tag, weight in self.taste_signals.items():
            if tag in tags:
                row['taste'] += weight
        if 'light' in tags or 'low-fat' in tags or \
                (row['protein_pct'] > 20 and row['total_fat_pct'] < 10):
            row['taste'] -= 2.0

        # 4. PRICE
        luxury_found = ingredients.intersection(self.luxury_ingredients)
        row['price'] += len(luxury_found) * 1.5
        if 'budget-friendly' in tags or 'cheap' in tags or \
                '5-ingredients-or-less' in tags or len(ingredients) <= 4:
            row['price'] -= 2.0

        # 5. MENTAL
        for tag, weight in self.mental_signals.items():
            if tag in tags:
                row['mental'] += weight
        if 'healthy' in tags or 'low-sodium' in tags or 'diabetic-friendly' in tags:
            row['mental'] -= 2.0

        # 6. MODIFICATION
        for tag, weight in self.mod_pos_signals.items():
            if tag in tags:
                row['modification'] += weight
        for tag, weight in self.mod_neg_signals.items():
            if tag in tags:
                row['modification'] += weight  # i pesi negativi sono gia nel dizionario

        return row

    def recommend(self, body=0.0, time=0.0, taste=0.0, price=0.0,
                  mental=0.0, modification=0.0, top_k=10):
        """FASE ONLINE: distanza euclidea tra vettore utente e vettori ricette."""
        if self.df_mood_vectors is None:
            raise ValueError("Il modello non e strutturato. Chiama .fit() prima.")

        user_vector = np.array([body, time, taste, price, mental, modification],
                               dtype=float)
        distances = np.linalg.norm(self.df_mood_vectors - user_vector, axis=1)

        df_result = self.df_recipes.copy()
        df_result['distance'] = distances
        df_top = df_result.sort_values(by='distance', ascending=True).head(top_k)

        output = []
        for _, row in df_top.iterrows():
            output.append({
                'id':                  int(row['id']),
                'name':                row['name'],
                'distanza_geometrica': round(float(row['distance']), 4),
                'mood_scores': {
                    'body':         round(float(row['body']), 2),
                    'time':         round(float(row['time']), 2),
                    'taste':        round(float(row['taste']), 2),
                    'price':        round(float(row['price']), 2),
                    'mental':       round(float(row['mental']), 2),
                    'modification': round(float(row['modification']), 2)
                },
                'minuti':  int(row['minutes']),
                'calorie': round(float(row['calories']), 1)
            })

        return output