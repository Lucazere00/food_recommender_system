import os
import sys
import pandas as pd
import numpy as np
from surprise import Dataset, Reader, SVD, NMF, KNNBasic
from surprise.model_selection import train_test_split
from surprise import accuracy
import collections

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import (PATH_CLEAN_RECIPES, PATH_CLEAN_INTERACTIONS,
                    SVD_N_FACTORS, SVD_N_EPOCHS, SVD_LR_ALL)


class CollaborativeFilteringRecommender:
    def __init__(self, min_user_interactions=5):
        self.min_user_interactions = min_user_interactions
        self.model = None
        self.df_recipes = None
        self.df_interactions = None
        self.trainset = None
        self.testset = None

    def fit(self, df_recipes, df_interactions):
        self.df_recipes = df_recipes.copy()
        self.df_interactions = df_interactions.copy()

        # 1. Filtro cold start
        user_counts  = self.df_interactions['user_id'].value_counts()
        active_users = user_counts[user_counts >= self.min_user_interactions].index
        df_filtered  = self.df_interactions[
            self.df_interactions['user_id'].isin(active_users)
        ].copy()
        print(f"-> Filtro Cold Start applicato. Righe rimanenti: {len(df_filtered)}")

        # 2. Split temporale (Leave-One-Out)
        df_filtered['date'] = pd.to_datetime(df_filtered['date'])
        df_filtered = df_filtered.sort_values(by='date')

        last_interaction_indices = df_filtered.groupby('user_id').tail(1).index
        df_test  = df_filtered.loc[last_interaction_indices]
        df_train = df_filtered.drop(last_interaction_indices)

        print(f"-> Split Temporale: Train={len(df_train)}, Test={len(df_test)}")

        # 3. Configurazione Surprise
        reader = Reader(rating_scale=(1, 5))
        train_data    = Dataset.load_from_df(
            df_train[['user_id', 'recipe_id', 'rating']], reader
        )
        self.trainset = train_data.build_full_trainset()
        self.testset  = list(
            df_test[['user_id', 'recipe_id', 'rating']].itertuples(
                index=False, name=None
            )
        )

        # 4. Addestramento SVD con parametri da config.py
        print("-> Addestramento SVD...")
        self.model = SVD(
            n_factors=SVD_N_FACTORS,
            n_epochs=SVD_N_EPOCHS,
            lr_all=SVD_LR_ALL,
            random_state=42
        )
        self.model.fit(self.trainset)
        print("-> Modello SVD addestrato con successo!")

    def evaluate_algorithms(self):
        """Confronta SVD, NMF, KNN User-based e KNN Item-based."""
        if self.trainset is None:
            raise ValueError("Esegui prima .fit().")

        algorithms = {
            'SVD':           SVD(n_factors=SVD_N_FACTORS, random_state=42),
            'NMF':           NMF(n_factors=SVD_N_FACTORS, random_state=42),
            'KNN User-based': KNNBasic(
                sim_options={'name': 'cosine', 'user_based': True}, verbose=False
            ),
            'KNN Item-based': KNNBasic(
                sim_options={'name': 'cosine', 'user_based': False}, verbose=False
            )
        }

        performance = {}
        print("\n=== BENCHMARK ALGORITMI ===")
        for name, algo in algorithms.items():
            algo.fit(self.trainset)
            predictions = algo.test(self.testset)
            rmse = accuracy.rmse(predictions, verbose=False)
            mae  = accuracy.mae(predictions, verbose=False)
            performance[name] = {'RMSE': round(rmse, 4), 'MAE': round(mae, 4)}
            print(f"{name:20s} -> RMSE: {rmse:.4f} | MAE: {mae:.4f}")

        return performance

    def recommend(self, user_id, top_k=10, popularity_fallback_model=None):
        if self.model is None:
            raise ValueError("Il modello non e strutturato. Chiama .fit() prima.")

        user_history = self.df_interactions[
            self.df_interactions['user_id'] == user_id
        ]

        # Gestione cold start
        if len(user_history) < self.min_user_interactions:
            print(f"Utente {user_id} in Cold Start "
                  f"({len(user_history)} interazioni). Attivazione fallback.")
            if popularity_fallback_model is not None:
                return popularity_fallback_model.recommend(top_k=top_k)
            else:
                raise ValueError(
                    "Utente in Cold Start: fornire un modello di popolarita come fallback."
                )

        seen_recipes  = set(user_history['recipe_id'].tolist())
        all_recipe_ids = self.df_recipes['id'].unique()

        predictions = []
        for r_id in all_recipe_ids:
            if r_id not in seen_recipes:
                pred_rating = self.model.predict(uid=user_id, iid=r_id).est
                predictions.append((r_id, pred_rating))

        predictions = sorted(predictions, key=lambda x: x[1], reverse=True)[:top_k]

        output = []
        for r_id, est_rating in predictions:
            recipe_meta = self.df_recipes[self.df_recipes['id'] == r_id].iloc[0]
            output.append({
                'id':               int(r_id),
                'name':             recipe_meta['name'],
                'rating_predetto':  round(float(est_rating), 2),
                'calorie':          round(float(recipe_meta['calories']), 1),
                'minuti':           int(recipe_meta['minutes'])
            })

        return output