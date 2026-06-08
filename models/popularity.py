import os
import sys
import pandas as pd
import ast

# Permette l'importazione dal file config posizionato nella cartella radice
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import PATH_CLEAN_RECIPES, PATH_CLEAN_INTERACTIONS

class PopularityRecommender:
    def __init__(self, m=50):
        """
        Inizializza il raccomandatore basato sulla popolarità (Bayesian Average).
        m: numero minimo di voti richiesto per dare fiducia alla media della ricetta.
        """
        self.m = m
        self.df_recipes = None
        self.df_interactions = None
        self.df_ranked = None
        self.global_mean_rating = 0.0
        
    def fit(self, df_recipes, df_interactions):
        """
        Calcola i punteggi di popolarità bayesiana sull'intero dataset.
        """
        self.df_recipes = df_recipes.copy()
        self.df_interactions = df_interactions.copy()
        
        # Se la colonna tags è ancora una stringa (letta da CSV), la convertiamo in lista
        if isinstance(self.df_recipes['tags'].iloc[0], str):
            self.df_recipes['tags'] = self.df_recipes['tags'].apply(lambda x: ast.literal_eval(x))
            
        # 1. Calcolo della media globale di tutti i rating (C)
        self.global_mean_rating = self.df_interactions['rating'].mean()
        C = self.global_mean_rating
        m = self.m
        
        # 2. Calcoliamo il numero di voti (v) e il rating medio (R) per ogni ricetta
        stats = self.df_interactions.groupby('recipe_id').agg(
            v=('rating', 'count'),
            R=('rating', 'mean')
        ).reset_index()
        
        # 3. Applichiamo la formula della Bayesian Average
        # score = (v / (v + m)) * R + (m / (v + m)) * C
        stats['score'] = (stats['v'] / (stats['v'] + m)) * stats['R'] + (m / (stats['v'] + m)) * C
        
        # 4. Uniamo le statistiche calcolate con i metadati delle ricette (id, nome, minuti, calorie)
        # Rinominiamo 'id' in 'recipe_id' temporaneamente per il merge
        recipes_meta = self.df_recipes[['id', 'name', 'minutes', 'calories', 'tags']].rename(columns={'id': 'recipe_id'})
        
        self.df_ranked = pd.merge(recipes_meta, stats, on='recipe_id', how='inner')
        
    def recommend(self, tag=None, top_k=10):
        """
        Restituisce le top-K ricette popolari, filtrando opzionalmente per un tag.
        """
        if self.df_ranked is None:
            raise ValueError("Il modello non è ancora stato addestrato. Chiama il metodo .fit() prima.")
            
        df_filtered = self.df_ranked
        
        # Se viene passato un tag, filtriamo tenendo solo le ricette che lo contengono
        if tag:
            # Pulizia stringa tag per evitare problemi di maiuscole/minuscole
            tag_clean = tag.lower().strip()
            df_filtered = df_filtered[df_filtered['tags'].apply(lambda tags_list: tag_clean in [t.lower() for t in tags_list])]
            
        # Ordiniamo per il punteggio Bayesiano decrescente
        df_top = df_filtered.sort_values(by='score', ascending=False).head(top_k)
        
        # Formattiamo l'output come lista di dizionari richiesto dall'obiettivo
        output = []
        for _, row in df_top.iterrows():
            output.append({
                'id': int(row['recipe_id']),
                'name': row['name'],
                'score': round(float(row['score']), 4),
                'rating_medio': round(float(row['R']), 2),
                'numero_voti': int(row['v']),
                'minuti': int(row['minutes']),
                'calorie': round(float(row['calories']), 1)
            })
            
        return output