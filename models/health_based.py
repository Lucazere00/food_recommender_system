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


class HealthBasedRecommender:
    def __init__(self):
        self.df_recipes = None
        self.global_stats = {}

        self.profiles = {
            'weight_loss': {
                'calories':      -0.6,
                'protein_pct':    0.4,
                'total_fat_pct': -0.2
            },
            'muscle_gain': {
                'calories':      0.2,
                'protein_pct':   0.7,
                'total_fat_pct': 0.1
            },
            'balanced': {
                'calories':      -0.2,
                'protein_pct':    0.4,
                'total_fat_pct': -0.2,
                'sodium_pct':    -0.2
            }
        }

    def fit(self, df_recipes):
        self.df_recipes = df_recipes.copy()
        self.df_recipes['tags'] = ensure_list_column(self.df_recipes['tags'])

        # Precalcola min/max globali per normalizzazione stabile
        for col in ['calories', 'protein_pct', 'total_fat_pct', 'sodium_pct']:
            if col in self.df_recipes.columns:
                self.global_stats[col] = {
                    'min': self.df_recipes[col].min(),
                    'max': self.df_recipes[col].max()
                }

    def _apply_hard_constraints(self, max_calories=None, min_protein_pct=None,
                                tags_required=None):
        df_filtered = self.df_recipes.copy()

        if max_calories is not None:
            df_filtered = df_filtered[df_filtered['calories'] <= max_calories]

        if min_protein_pct is not None:
            df_filtered = df_filtered[df_filtered['protein_pct'] >= min_protein_pct]

        if tags_required:
            for tag in tags_required:
                tag_clean = tag.lower().strip()
                df_filtered = df_filtered[
                    df_filtered['tags'].apply(
                        lambda tags_list: tag_clean in [t.lower() for t in tags_list]
                    )
                ]

        return df_filtered

    def _calculate_soft_score(self, df_candidates, profile_name='balanced'):
        if df_candidates.empty:
            return df_candidates

        df_scored = df_candidates.copy()
        weights = self.profiles.get(profile_name, self.profiles['balanced'])

        df_scored['health_score'] = 0.0

        for macro, weight in weights.items():
            if macro in df_scored.columns and macro in self.global_stats:
                min_val = self.global_stats[macro]['min']
                max_val = self.global_stats[macro]['max']

                if max_val != min_val:
                    norm_macro = (df_scored[macro] - min_val) / (max_val - min_val)
                else:
                    norm_macro = 0.0

                df_scored['health_score'] += norm_macro * weight

        return df_scored

    def recommend(self, max_calories=None, min_protein_pct=None, tags_required=None,
                  profile_name='balanced', top_k=10):
        if self.df_recipes is None:
            raise ValueError("Il modello non e strutturato. Chiama .fit() prima.")

        df_candidates = self._apply_hard_constraints(max_calories, min_protein_pct,
                                                     tags_required)

        if df_candidates.empty:
            print("Nessuna ricetta trovata con i vincoli specificati.")
            return []

        df_scored = self._calculate_soft_score(df_candidates, profile_name)
        df_top = df_scored.sort_values(by='health_score', ascending=False).head(top_k)

        output = []
        for _, row in df_top.iterrows():
            output.append({
                'id':           int(row['id']),
                'name':         row['name'],
                'health_score': round(float(row['health_score']), 4),
                'calories':     round(float(row['calories']), 1),
                'protein_pdv':  round(float(row['protein_pct']), 1),
                'fat_pdv':      round(float(row['total_fat_pct']), 1),
                'minuti':       int(row['minutes'])
            })
        return output

    def generate_weekly_plan(self, max_calories=None, min_protein_pct=None,
                             tags_required=None, profile_name='balanced',
                             days=7, random_seed=None):
        if self.df_recipes is None:
            raise ValueError("Il modello non e strutturato. Chiama .fit() prima.")

        df_candidates = self._apply_hard_constraints(max_calories, min_protein_pct,
                                                     tags_required)
        df_scored = self._calculate_soft_score(df_candidates, profile_name)

        if len(df_scored) < days:
            raise ValueError(
                f"Solo {len(df_scored)} ricette disponibili con questi vincoli. "
                f"Impossibile generare un piano di {days} giorni senza ripetizioni."
            )

        df_pool = df_scored.sort_values(by='health_score', ascending=False).head(50).copy()
        df_plan = df_pool.sample(n=days, random_state=random_seed)

        days_names = [f"Giorno {i+1}" for i in range(days)]
        if days == 7:
            days_names = ["Lunedi", "Martedi", "Mercoledi", "Giovedi",
                          "Venerdi", "Sabato", "Domenica"]

        weekly_plan = {}
        for i, (_, row) in enumerate(df_plan.iterrows()):
            weekly_plan[days_names[i]] = {
                'id':           int(row['id']),
                'name':         row['name'],
                'health_score': round(float(row['health_score']), 4),
                'calories':     round(float(row['calories']), 1),
                'protein_pdv':  round(float(row['protein_pct']), 1),
                'fat_pdv':      round(float(row['total_fat_pct']), 1),
                'minuti':       int(row['minutes'])
            }

        return weekly_plan