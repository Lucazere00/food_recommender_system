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
    DISTANZA_MASSIMA = (6 * 10**2) ** 0.5

    def __init__(self):
        self.df_recipes = None
        self.df_mood_vectors = None
        self.distanza_riferimento = None
        self.n_ingredients_median = 0.0
        self.n_ingredients_iqr = 1.0
        self.n_steps_median = 0.0
        self.n_steps_iqr = 1.0
        self.ingredient_frequency = {}
        self.max_ingredient_frequency = 1

        self.luxury_ingredients = {
            'lobster', 'truffle', 'wagyu', 'caviar', 'saffron',
            'ribeye', 'shrimp', 'prosciutto'
        }

        # Pesi differenziati per segnale (piu difendibili di un +2.0 fisso)
        self.body_signals    = {'comfort-food': 2.0, 'main-dish': 1.2,
                                'meat': 1.0, 'beef': 0.8, 'pork': 0.8}
        self.mental_signals  = {'comfort-food': 2.0, 'kid-friendly': 1.2,
                                'chocolate': 1.5, 'desserts': 1.5}
        self.taste_signals   = {'cheese': 1.5, 'savory': 1.2,
                                'sweet': 1.0, 'spicy': 1.0}
        self.mod_pos_signals = {'asian': 1.8, 'mexican': 1.6, 'indian': 1.4,
                                'thai': 1.2, 'chinese': 1.2,
                                'middle-eastern': 1.2}
        self.mod_neg_signals = {'comfort-food': -1.0}

    def fit(self, df_recipes):
        """FASE OFFLINE: calcola il vettore a 6 dimensioni per ogni ricetta."""
        self.df_recipes = df_recipes.copy()

        self.df_recipes['tags']        = ensure_list_column(self.df_recipes['tags'])
        self.df_recipes['ingredients'] = ensure_list_column(self.df_recipes['ingredients'])
        self.n_ingredients_median = float(self.df_recipes['n_ingredients'].median())
        self.n_steps_median = float(self.df_recipes['n_steps'].median())
        self.n_ingredients_iqr = self._safe_iqr(self.df_recipes['n_ingredients'])
        self.n_steps_iqr = self._safe_iqr(self.df_recipes['n_steps'])
        ingredient_counts = {}
        for ingredient_list in self.df_recipes['ingredients']:
            for ingredient in set(str(i).lower().strip() for i in ingredient_list):
                ingredient_counts[ingredient] = ingredient_counts.get(ingredient, 0) + 1
        self.ingredient_frequency = ingredient_counts
        self.max_ingredient_frequency = max(ingredient_counts.values(), default=1)

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
        self.distanza_riferimento = self._estimate_reference_distance()
        print("-> Matrice Mood generata e normalizzata in scala [-5, +5]!")
        print(f"-> Distanza empirica di riferimento (p90): {self.distanza_riferimento:.4f}")

    @staticmethod
    def _safe_iqr(series):
        iqr = float(series.quantile(0.75) - series.quantile(0.25))
        return iqr if iqr > 0 else 1.0

    @staticmethod
    def _clamp01(value):
        return min(1.0, max(0.0, float(value)))

    def _estimate_reference_distance(self, sample_size=2000, random_state=42):
        n_recipes = len(self.df_mood_vectors)
        if n_recipes < 2:
            return self.DISTANZA_MASSIMA

        rng = np.random.default_rng(random_state)
        pair_count = min(sample_size, n_recipes * (n_recipes - 1) // 2)
        left = rng.integers(0, n_recipes, size=pair_count)
        right = rng.integers(0, n_recipes - 1, size=pair_count)
        right = right + (right >= left)
        distances = np.linalg.norm(self.df_mood_vectors[left] - self.df_mood_vectors[right], axis=1)
        reference = float(np.percentile(distances, 90))
        return reference if reference > 0 else self.DISTANZA_MASSIMA

    def _ingredient_commonness(self, ingredients):
        if not ingredients:
            return 0.0
        max_log_frequency = np.log1p(self.max_ingredient_frequency)
        if max_log_frequency == 0:
            return 0.0
        frequencies = [
            np.log1p(self.ingredient_frequency.get(ingredient, 0)) / max_log_frequency
            for ingredient in ingredients
        ]
        return float(np.mean(frequencies))

    def _classic_familiarity(self, row):
        ingredient_simplicity = self._clamp01(
            (self.n_ingredients_median - row['n_ingredients']) /
            max(self.n_ingredients_median, 1.0)
        )
        step_simplicity = self._clamp01(
            (self.n_steps_median - row['n_steps']) / max(self.n_steps_median, 1.0)
        )
        return (ingredient_simplicity + step_simplicity) / 2

    def _compute_recipe_mood(self, row):
        """Calcola i punteggi grezzi di una singola ricetta."""
        tags        = set([t.lower().strip() for t in row['tags']])
        ingredients = set([i.lower().strip() for i in row['ingredients']])

        # 1. BODY
        for tag, weight in self.body_signals.items():
            if tag in tags:
                row['body'] += weight
        row['body'] += 2.0 * self._clamp01((row['calories'] - 300) / 600)
        if 'light' in tags or 'salad' in tags or 'low-calorie' in tags \
                or row['calories'] < 300:
            row['body'] -= 2.0 * self._clamp01((300 - row['calories']) / 300)

        # 2. TIME
        row['time'] += 1.2 * self._clamp01(row['minutes'] / 120)
        row['time'] += 0.8 * self._clamp01(row['n_steps'] / 20)
        if '15-minutes-or-less' in tags or '30-minutes-or-less' in tags \
                or row['minutes'] <= 60:
            row['time'] -= 2.0 * self._clamp01((60 - row['minutes']) / 60)

        # 3. TASTE
        row['taste'] += 1.5 * self._clamp01(
            max(row['total_fat_pct'], row['sugar_pct']) / 60
        )
        for tag, weight in self.taste_signals.items():
            if tag in tags:
                row['taste'] += weight
        if 'light' in tags or 'low-fat' in tags or \
                (row['protein_pct'] > 20 and row['total_fat_pct'] < 10):
            row['taste'] -= 2.0

        # 4. PRICE
        luxury_found = ingredients.intersection(self.luxury_ingredients)
        row['price'] += 2.5 * self._clamp01(len(luxury_found) / 2)
        budget_tag_bonus = 0.25 if (
            'budget-friendly' in tags or 'cheap' in tags or '5-ingredients-or-less' in tags
        ) else 0.0
        ingredient_simplicity = self._clamp01((8 - row['n_ingredients']) / 7)
        ingredient_commonness = self._ingredient_commonness(ingredients)
        row['price'] -= 2.0 * self._clamp01(
            0.7 * ingredient_simplicity + 0.3 * ingredient_commonness + budget_tag_bonus
        )

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
        if 'north-american' in tags:
            row['modification'] -= 1.5
        classic_familiarity = self._classic_familiarity(row)
        for tag, weight in self.mod_neg_signals.items():
            if tag in tags:
                row['modification'] += weight * (0.75 + 0.25 * classic_familiarity)
        ingredient_complexity = (
            row['n_ingredients'] - self.n_ingredients_median
        ) / self.n_ingredients_iqr
        step_complexity = (row['n_steps'] - self.n_steps_median) / self.n_steps_iqr
        row['modification'] += 0.6 * self._clamp01(ingredient_complexity / 2)
        row['modification'] += 0.6 * self._clamp01(step_complexity / 2)

        return row

    def recommend(self, body=0.0, time=0.0, taste=0.0, price=0.0,
                  mental=0.0, modification=0.0, top_k=10):
        """FASE ONLINE: distanza euclidea tra vettore utente e vettori ricette."""
        if self.df_mood_vectors is None:
            raise ValueError("Il modello non e strutturato. Chiama .fit() prima.")

        user_vector = np.array([body, time, taste, price, mental, modification],
                               dtype=float)
        distances = np.linalg.norm(self.df_mood_vectors - user_vector, axis=1)
        reference_distance = self.distanza_riferimento or self.DISTANZA_MASSIMA

        df_result = self.df_recipes.copy()
        df_result['distance'] = distances
        df_top = df_result.sort_values(by='distance', ascending=True).head(top_k)

        output = []
        for _, row in df_top.iterrows():
            output.append({
                'id':                  int(row['id']),
                'name':                row['name'],
                'distanza_geometrica': round(float(row['distance']), 4),
                'affinita_pct':        round(100 * max(0, 1 - row['distance'] / reference_distance), 1),
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
