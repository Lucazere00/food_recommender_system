import os
import sys
import pandas as pd
import numpy as np

class HybridRecommender:
    def __init__(self, popularity_model, content_model, mood_model, cf_model, health_model):
        """
        Inizializza il Recommender Ibrido aggregando i 5 sotto-modelli sviluppati.
        """
        self.pop_model = popularity_model
        self.content_model = content_model
        self.mood_model = mood_model
        self.cf_model = cf_model
        self.health_model = health_model
        
    def _minmax_scale_dict(self, score_dict, invert=False):
        """
        Normalizza i punteggi di un dizionario nell'intervallo [0, 1].
        Se invert=True (es. per le distanze geometriche), i valori più bassi diventano 1 e i più alti 0.
        """
        if not score_dict:
            return {}
        
        ids = list(score_dict.keys())
        values = np.array(list(score_dict.values()), dtype=float)
        
        min_val = values.min()
        max_val = values.max()
        
        if max_val != min_val:
            scaled_values = (values - min_val) / (max_val - min_val)
        else:
            scaled_values = np.ones_like(values)
            
        if invert:
            scaled_values = 1.0 - scaled_values
            
        return dict(zip(ids, scaled_values))

    def recommend(self, user_id=None, user_ingredients=None, mood_params=None, health_params=None, 
                  weights=None, top_k=10):
        """
        FASE ONLINE: Calcola lo score ibrido context-aware e restituisce le top-K ricette.
        """
        # 1. DETERMINAZIONE AUTOMATICA DEI PESI (Context-Aware Fallback)
        if weights is None:
            weights = {'alpha_mood': 0.0, 'beta_content': 0.0, 'gamma_cf': 0.0, 'delta_health': 0.0, 'epsilon_pop': 0.0}
            
            # Controllo Cold Start per CF
            is_cold_start = True
            if user_id is not None:
                user_hist = self.cf_model.df_interactions[self.cf_model.df_interactions['user_id'] == user_id]
                if len(user_hist) >= self.cf_model.min_user_interactions:
                    is_cold_start = False
            
            # Scenario A: Nuovo Utente (Cold Start)
            if is_cold_start:
                weights['epsilon_pop'] = 0.4
                weights['alpha_mood'] = 0.6 if mood_params else 0.0
                if mood_params is None: weights['epsilon_pop'] = 1.0
            # Scenario B: Utente registrato
            else:
                weights['gamma_cf'] = 0.6
                weights['alpha_mood'] = 0.4 if mood_params else 0.0
                if mood_params is None: weights['gamma_cf'] = 1.0
                
            # Se vengono inseriti ingredienti (Svuota-frigo attivo), rimodula i pesi per dar spazio al Content
            if user_ingredients:
                for k in weights: weights[k] *= 0.5  # Abbassa proporzionalmente gli altri
                weights['beta_content'] = 0.5
                
            # Se ci sono filtri salutistici, assegna un peso di rinforzo allo score health
            if health_params and health_params.get('profile_name'):
                for k in weights: weights[k] *= 0.8
                weights['delta_health'] = 0.2

        # Normalizzazione dei pesi in modo che la somma sia esattamente 1
        total_w = sum(weights.values())
        if total_w > 0:
            weights = {k: v / total_w for k, v in weights.items()}
        
        # 2. RACCOLTA PUNTEGGI DAI SOTTO-MODELLI
        # Recuperiamo un pool ampio di ricette candidate da ogni modello attivo (es. top-200)
        pool_size = 200
        scores_mood, scores_content, scores_cf, scores_health, scores_pop = {}, {}, {}, {}, {}
        
        # Estrarre Popularity
        pop_res = self.pop_model.recommend(top_k=pool_size)
        scores_pop = {r['id']: r['score'] for r in pop_res}
        
        # Estrarre Mood
        if mood_params and weights['alpha_mood'] > 0:
            mood_res = self.mood_model.recommend(**mood_params, top_k=pool_size)
            scores_mood = {r['id']: r['distanza_geometrica'] for r in mood_res}
            
        # Estrarre Content (Svuota-frigo)
        if user_ingredients and weights['beta_content'] > 0:
            cont_res = self.content_model.recommend(user_ingredients, top_k=pool_size, max_missing_ingredients=3)
            scores_content = {r['id']: r['similarity'] for r in cont_res}
            
        # Estrarre Collaborative Filtering (Solo se non in Cold Start)
        if user_id is not None and weights['gamma_cf'] > 0:
            try:
                cf_res = self.cf_model.recommend(user_id=user_id, top_k=pool_size)
                scores_cf = {r['id']: r['rating_predetto'] for r in cf_res}
            except ValueError:
                pass # Gestito dal context-aware che ha azzerato gamma_cf se in cold start
                
        # Estrarre Health Score
        if health_params and weights['delta_health'] > 0:
            h_res = self.health_model.recommend(**health_params, top_k=pool_size)
            scores_health = {r['id']: r['health_score'] for r in h_res}

        # 3. NORMALIZZAZIONE DEI PUNTEGGI PARZIALI IN SCALA [0, 1]
        norm_pop = self._minmax_scale_dict(scores_pop)
        norm_mood = self._minmax_scale_dict(scores_mood, invert=True) # Distanza minore = score vicino a 1
        norm_content = self._minmax_scale_dict(scores_content)
        norm_cf = self._minmax_scale_dict(scores_cf)
        norm_health = self._minmax_scale_dict(scores_health)
        
        # 4. AGGREGAZIONE LINEARE PESATA
        # Il paniere dei candidati totali è l'unione di tutti gli ID emersi
        all_candidate_ids = set(norm_pop.keys()) | set(norm_mood.keys()) | set(norm_content.keys()) | set(norm_cf.keys()) | set(norm_health.keys())
        
        hybrid_scores = []
        for r_id in all_candidate_ids:
            # Se un modello non ha intercettato quella ricetta nel suo pool, assume il valore minimo (0.0)
            s_mood = norm_mood.get(r_id, 0.0)
            s_cont = norm_content.get(r_id, 0.0)
            s_cf = norm_cf.get(r_id, 0.0)
            s_health = norm_health.get(r_id, 0.0)
            s_pop = norm_pop.get(r_id, 0.0)
            
            # Formula pesata: score_finale = α·score_mood + β·score_content + γ·score_CF + δ·score_health + ε·score_popularity
            final_score = (
                weights['alpha_mood'] * s_mood +
                weights['beta_content'] * s_cont +
                weights['gamma_cf'] * s_cf +
                weights['delta_health'] * s_health +
                weights['epsilon_pop'] * s_pop
            )
            hybrid_scores.append((r_id, final_score))
            
        # 5. ORDINAMENTO E COSTRUZIONE METADATI OUTPUT
        hybrid_scores = sorted(hybrid_scores, key=lambda x: x[1], reverse=True)[:top_k]
        
        output = []
        for r_id, f_score in hybrid_scores:
            recipe_meta = self.pop_model.df_recipes[self.pop_model.df_recipes['id'] == r_id].iloc[0]
            output.append({
                'id': int(r_id),
                'name': recipe_meta['name'],
                'score_ibrido_finale': round(float(f_score), 4),
                'calorie': round(float(recipe_meta['calories']), 1),
                'minuti': int(recipe_meta['minutes'])
            })
            
        return output