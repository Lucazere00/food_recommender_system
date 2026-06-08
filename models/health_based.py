import os
import sys
import pandas as pd
import numpy as np
import ast

# Permette l'importazione dal file config posizionato nella cartella radice
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import PATH_CLEAN_RECIPES

class HealthBasedRecommender:
    def __init__(self):
        """
        Inizializza il Recommender Salutistico.
        Definisce i profili nutrizionali (soft constraints) tramite dizionari di pesi.
        I macronutrienti nel dataset sono espressi in % Daily Value (PDV).
        """
        self.df_recipes = None
        
        # Profili nutrizionali: definiscono i pesi da dare ai macro nell'ordinamento soft
        # Valori positivi premiano il macro, valori negativi lo penalizzano
        self.profiles = {
            'weight_loss': {
                'calories': -0.6,      # Penalizza fortemente le calorie alte
                'protein_pct': 0.4,   # Premia le proteine alte (sazietà/muscolo)
                'total_fat_pct': -0.2 # Penalizza i grassi alti
            },
            'muscle_gain': {
                'calories': 0.2,       # Ammette un surplus calorico moderato
                'protein_pct': 0.7,   # Focus massiccio sulle proteine
                'total_fat_pct': 0.1  # Grasso neutro/moderato
            },
            'balanced': {
                'calories': -0.2,      # Controllo calorico leggero
                'protein_pct': 0.4,   # Buon apporto proteico
                'total_fat_pct': -0.2, # Controllo dei grassi
                'sodium_pct': -0.2    # Controllo del sodio (salute cardiovascolare)
            }
        }

    def fit(self, df_recipes):
        """
        Carica il dataset delle ricette e normalizza i tag.
        """
        self.df_recipes = df_recipes.copy()
        
        # Assicuriamoci che la colonna tags sia una vera lista Python
        if isinstance(self.df_recipes['tags'].iloc[0], str):
            self.df_recipes['tags'] = self.df_recipes['tags'].apply(lambda x: ast.literal_eval(x))

    def _apply_hard_constraints(self, max_calories=None, min_protein_pct=None, tags_required=None):
        """
        Applica i filtri booleani rigidi escludendo le ricette non idonee.
        """
        df_filtered = self.df_recipes.copy()
        
        # 1. Filtro calorico massimo (kcal assolute)
        if max_calories is not None:
            df_filtered = df_filtered[df_filtered['calories'] <= max_calories]
            
        # 2. Filtro proteico minimo (% Daily Value)
        if min_protein_pct is not None:
            df_filtered = df_filtered[df_filtered['protein_pct'] >= min_protein_pct]
            
        # 3. Filtro sui tag dietetici (es. vegan, vegetarian, gluten-free, dairy-free)
        if tags_required:
            for tag in tags_required:
                tag_clean = tag.lower().strip()
                df_filtered = df_filtered[df_filtered['tags'].apply(lambda tags_list: tag_clean in [t.lower() for t in tags_list])]
                
        return df_filtered

    def _calculate_soft_score(self, df_candidates, profile_name='balanced'):
        """
        Calcola lo score nutrizionale personalizzato in base al profilo scelto dall'utente.
        Usa z-score (normalizzazione) per evitare che le calorie schiaccino le percentuali dei macro.
        """
        if df_candidates.empty:
            return df_candidates
            
        df_scored = df_candidates.copy()
        weights = self.profiles.get(profile_name, self.profiles['balanced'])
        
        # Inizializziamo lo score a 0
        df_scored['health_score'] = 0.0
        
        # Applichiamo i pesi linearmente normalizzando le colonne per evitare problemi di unità di misura diversi
        for macro, weight in weights.items():
            if macro in df_scored.columns:
                # Calcoliamo la normalizzazione (MinMax) per portare ogni macro in scala 0-1
                min_val = df_scored[macro].min()
                max_val = df_scored[macro].max()
                
                if max_val != min_val:
                    norm_macro = (df_scored[macro] - min_val) / (max_val - min_val)
                else:
                    norm_macro = 0.0
                    
                df_scored['health_score'] += norm_macro * weight
                
        return df_scored

    def recommend(self, max_calories=None, min_protein_pct=None, tags_required=None, profile_name='balanced', top_k=10):
        """
        Restituisce le top-K ricette che rispettano i vincoli hard ordinati per score nutrizionale.
        """
        if self.df_recipes is None:
            raise ValueError("Il modello non è strutturato. Chiama .fit() prima.")
            
        # 1. Applica i vincoli hard
        df_candidates = self._apply_hard_constraints(max_calories, min_protein_pct, tags_required)
        
        if df_candidates.empty:
            return []
            
        # 2. Applica i vincoli soft (scoring)
        df_scored = self._calculate_soft_score(df_candidates, profile_name)
        
        # 3. Ordina per score decrescente
        df_top = df_scored.sort_values(by='health_score', ascending=False).head(top_k)
        
        # Formattazione output
        output = []
        for _, row in df_top.iterrows():
            output.append({
                'id': int(row['id']),
                'name': row['name'],
                'health_score': round(float(row['health_score']), 4),
                'calories': round(float(row['calories']), 1),
                'protein_pdv': round(float(row['protein_pct']), 1),
                'fat_pdv': round(float(row['total_fat_pct']), 1),
                'minuti': int(row['minutes'])
            })
        return output

    def generate_weekly_plan(self, max_calories=None, min_protein_pct=None, tags_required=None, profile_name='balanced', days=7):
        """
        Genera un piano alimentare per N giorni campionando senza ripetizioni dalle top-50 ricette idonee.
        """
        if self.df_recipes is None:
            raise ValueError("Il modello non è strutturato. Chiama .fit() prima.")
            
        # 1. Ottieni tutte le ricette idonee e ordinate per score nutrizionale
        df_candidates = self._apply_hard_constraints(max_calories, min_protein_pct, tags_required)
        df_scored = self._calculate_soft_score(df_candidates, profile_name)
        
        if len(df_scored) < days:
            raise ValueError(f"Ci sono solo {len(df_scored)} ricette disponibili con questi vincoli. Impossibile generare un piano di {days} giorni senza ripetizioni.")
            
        # Prendiamo il bacino delle top-50 migliori ricette per garantire qualità nutrizionale ma anche varietà
        df_pool = df_scored.sort_values(by='health_score', ascending=False).head(50).copy()
        
        # Campioniamo in modo casuale senza ripetizione 'days' ricette dal pool delle top-50
        df_plan = df_pool.sample(n=days, random_state=None) # random_state=None per cambiare piano a ogni click
        
        days_names = [f"Giorno {i+1}" for i in range(days)]
        if days == 7:
            days_names = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
            
        weekly_plan = {}
        for i, (_, row) in enumerate(df_plan.iterrows()):
            weekly_plan[days_names[i]] = {
                'id': int(row['id']),
                'name': row['name'],
                'health_score': round(float(row['health_score']), 4),
                'calories': round(float(row['calories']), 1),
                'protein_pdv': round(float(row['protein_pct']), 1),
                'fat_pdv': round(float(row['total_fat_pct']), 1),
                'minuti': int(row['minutes'])
            }
            
        return weekly_plan