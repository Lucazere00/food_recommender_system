import os
import sys
import pandas as pd
import numpy as np
from surprise import Dataset, Reader, SVD, NMF, KNNBasic
from surprise.model_selection import train_test_split
from surprise import accuracy
import collections

# Permette l'importazione dal file config posizionato nella cartella radice
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import PATH_CLEAN_RECIPES, PATH_CLEAN_INTERACTIONS

class CollaborativeFilteringRecommender:
    def __init__(self, min_user_interactions=5):
        """
        Inizializza il Recommender basato su Filtro Collaborativo.
        min_user_interactions: soglia sotto la quale l'utente viene considerato in 'Cold Start'
        """
        self.min_user_interactions = min_user_interactions
        self.model = None
        self.df_recipes = None
        self.df_interactions = None
        self.trainset = None
        self.testset = None
        
    def fit(self, df_recipes, df_interactions):
        """
        Prepara i dati con split temporale e addestra il modello SVD definitivo.
        """
        self.df_recipes = df_recipes.copy()
        self.df_interactions = df_interactions.copy()
        
        # 1. Filtriamo gli utenti con troppe poche interazioni (Pulizia della matrice)
        user_counts = self.df_interactions['user_id'].value_counts()
        active_users = user_counts[user_counts >= self.min_user_interactions].index
        df_filtered = self.df_interactions[self.df_interactions['user_id'].isin(active_users)].copy()
        
        print(f"-> Filtro Cold Start applicato. Righe rimanenti: {len(df_filtered)}")
        
        # 2. Split Temporale (Leave-One-Out temporale)
        # Ordiniamo per data per prendere l'ultima interazione di ogni utente
        df_filtered['date'] = pd.to_datetime(df_filtered['date'])
        df_filtered = df_filtered.sort_values(by='date')
        
        # L'ultima riga di ogni utente va nel test set, il resto nel train set
        df_test = df_filtered.groupby('user_id').last().reset_index()
        
        # Il train set contiene tutte le righe tranne quelle selezionate per il test set
        # Creiamo un indice combinato per fare il drop corretto
        test_indices = df_test.index
        df_train = df_filtered.drop(df_filtered.groupby('user_id').tail(1).index)
        
        print(f"-> Split Temporale completato. Train size: {len(df_train)}, Test size: {len(df_test)}")
        
        # 3. Configurazione per Surprise
        reader = Reader(rating_scale=(1, 5))
        
        # Carichiamo il dataset combinato e lo split in Surprise formato
        train_data = Dataset.load_from_df(df_train[['user_id', 'recipe_id', 'rating']], reader)
        self.trainset = train_data.build_full_trainset()
        
        # Il testset in Surprise deve essere una lista di tuple (user, item, rating)
        self.testset = list(df_test[['user_id', 'recipe_id', 'rating']].itertuples(index=False, name=None))
        
        # 4. Addestramento del benchmark principale (SVD con Bias attivo)
        print("-> Addestramento dell'algoritmo SVD definitivo...")
        self.model = SVD(n_factors=50, n_epochs=20, lr_all=0.005, random_state=42)
        self.model.fit(self.trainset)
        print("-> Modello SVD addestrato con successo!")

    def evaluate_algorithms(self):
        """
        Compara i diversi algoritmi (SVD, NMF, KNN User, KNN Item) calcolando RMSE e MAE.
        """
        if self.trainset is None:
            raise ValueError("Esegui prima il metodo .fit() per preparare i dati.")
            
        algorithms = {
            'SVD (Fattori Latenti)': SVD(n_factors=50, random_state=42),
            'NMF (Matrice Non-Negativa)': NMF(n_factors=50, random_state=42),
            'KNN User-Based': KNNBasic(sim_options={'name': 'cosine', 'user_based': True}, verbose=False),
            'KNN Item-Based': KNNBasic(sim_options={'name': 'cosine', 'user_based': False}, verbose=False)
        }
        
        performance = {}
        print("\n=== AVVIO BENCHMARK ALGORITMI (SURPRISE) ===")
        for name, algo in algorithms.items():
            algo.fit(self.trainset)
            predictions = algo.test(self.testset)
            
            rmse = accuracy.rmse(predictions, verbose=False)
            mae = accuracy.mae(predictions, verbose=False)
            
            performance[name] = {'RMSE': round(rmse, 4), 'MAE': round(mae, 4)}
            print(f"{name} -> RMSE: {rmse:.4f} | MAE: {mae:.4f}")
            
        return performance

    def recommend(self, user_id, top_k=10, popularity_fallback_model=None):
        """
        Restituisce le top-K ricette predette per un utente, gestendo il Cold Start.
        """
        if self.model is None:
            raise ValueError("Il modello non è strutturato. Chiama .fit() prima.")
            
        # --- GESTIONE COLD START (FALLBACK) ---
        # Controlliamo se l'utente esiste nel database storico e quante interazioni ha
        user_history = self.df_interactions[self.df_interactions['user_id'] == user_id]
        
        if len(user_history) < self.min_user_interactions:
            print(f"⚠️ UTENTE {user_id} IN COLD START ({len(user_history)} interazioni). Attivazione Fallback Popolarità!")
            if popularity_fallback_model is not None:
                return popularity_fallback_model.recommend(top_k=top_k)
            else:
                raise ValueError("L'utente è in Cold Start, ma non è stato fornito un modello di popolarità come fallback.")
        
        # --- FILTRO COLLABORATIVO REALE (UTENTE REGISTRATO) ---
        # 1. Troviamo gli ID di tutte le ricette già viste/votate dall'utente per non raccomandargliele di nuovo
        seen_recipes = set(user_history['recipe_id'].tolist())
        
        # 2. Prendiamo la lista di tutte le ricette uniche nel catalogo
        all_recipe_ids = self.df_recipes['id'].unique()
        
        predictions = []
        # 3. Prediciamo il voto per ciascuna ricetta che l'utente NON ha ancora visto
        for r_id in all_recipe_ids:
            if r_id not in seen_recipes:
                # model.predict restituisce un oggetto Prediction; .est contiene il voto stimato (1-5)
                pred_rating = self.model.predict(uid=user_id, iid=r_id).est
                predictions.append((r_id, pred_rating))
                
        # 4. Ordiniamo le predizioni in base al rating stimato decrescente
        predictions = sorted(predictions, key=lambda x: x[1], reverse=True)[:top_k]
        
        # Formattiamo l'output estraendo i metadati delle ricette
        output = []
        for r_id, est_rating in predictions:
            recipe_meta = self.df_recipes[self.df_recipes['id'] == r_id].iloc[0]
            output.append({
                'id': int(r_id),
                'name': recipe_meta['name'],
                'rating_predetto': round(float(est_rating), 2),
                'calorie': round(float(recipe_meta['calories']), 1),
                'minuti': int(recipe_meta['minutes'])
            })
            
        return output