import os
import sys
import pandas as pd
import numpy as np
import ast

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import PATH_CLEAN_RECIPES, PATH_CLEAN_INTERACTIONS


def ensure_list_column(series):
    """Converte una colonna di stringhe-lista in vere liste Python in modo sicuro."""
    if series.empty:
        return series
    first_valid = series.dropna().iloc[0] if not series.dropna().empty else None
    if first_valid is None or isinstance(first_valid, list):
        return series
    return series.apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else [])


class PopularityRecommender:
    def __init__(self, m=50):
        """
        Inizializza il raccomandatore basato sulla popolarita (Bayesian Average).
        m: numero minimo di voti richiesto per dare fiducia alla media della ricetta.
        """
        self.m = m
        self.df_recipes = None
        self.df_interactions = None
        self.df_ranked = None
        self.global_mean_rating = 0.0

    def fit(self, df_recipes, df_interactions):
        """
        Calcola i punteggi di popolarita bayesiana sull'intero dataset.
        """
        self.df_recipes = df_recipes.copy()
        self.df_interactions = df_interactions.copy()

        self.df_recipes['tags'] = ensure_list_column(self.df_recipes['tags'])

        # 1. Calcolo della media globale di tutti i rating (C)
        self.global_mean_rating = self.df_interactions['rating'].mean()
        C = self.global_mean_rating
        m = self.m

        # 2. Calcolo numero di voti (v) e rating medio (R) per ogni ricetta
        stats = self.df_interactions.groupby('recipe_id').agg(
            v=('rating', 'count'),
            R=('rating', 'mean')
        ).reset_index()

        # 3. Bayesian Average: score = (v / (v + m)) * R + (m / (v + m)) * C
        stats['score'] = (stats['v'] / (stats['v'] + m)) * stats['R'] + \
                         (m / (stats['v'] + m)) * C

        # 4. Merge con i metadati delle ricette
        recipes_meta = self.df_recipes[['id', 'name', 'minutes', 'calories', 'tags']].rename(
            columns={'id': 'recipe_id'}
        )
        self.df_ranked = pd.merge(recipes_meta, stats, on='recipe_id', how='inner')

    def recommend(self, tag=None, top_k=10):
        """
        Restituisce le top-K ricette popolari, filtrando opzionalmente per un tag.
        """
        if self.df_ranked is None:
            raise ValueError("Il modello non e ancora stato addestrato. Chiama .fit() prima.")

        df_filtered = self.df_ranked.copy()

        if tag:
            tag_clean = tag.lower().strip()
            df_filtered = df_filtered[
                df_filtered['tags'].apply(
                    lambda tags_list: tag_clean in [t.lower() for t in tags_list]
                )
            ]

        if df_filtered.empty:
            print(f"Nessuna ricetta trovata con il tag '{tag}'.")
            return []

        df_top = df_filtered.sort_values(by='score', ascending=False).head(top_k)

        output = []
        for _, row in df_top.iterrows():
            output.append({
                'id':           int(row['recipe_id']),
                'name':         row['name'],
                'score':        round(float(row['score']), 4),
                'rating_medio': round(float(row['R']), 2),
                'numero_voti':  int(row['v']),
                'minuti':       int(row['minutes']),
                'calorie':      round(float(row['calories']), 1)
            })

        return output