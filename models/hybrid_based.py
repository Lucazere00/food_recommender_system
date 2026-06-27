import os
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class HybridRecommender:
    def __init__(self, popularity_model, content_model, mood_model,
                 cf_model, health_model):
        self.pop_model     = popularity_model
        self.content_model = content_model
        self.mood_model    = mood_model
        self.cf_model      = cf_model
        self.health_model  = health_model

    def _minmax_scale_dict(self, score_dict, invert=False):
        if not score_dict:
            return {}
        ids    = list(score_dict.keys())
        values = np.array(list(score_dict.values()), dtype=float)
        min_val, max_val = values.min(), values.max()
        if max_val != min_val:
            scaled = (values - min_val) / (max_val - min_val)
        else:
            scaled = np.ones_like(values)
        if invert:
            scaled = 1.0 - scaled
        return dict(zip(ids, scaled))

    def recommend(self, user_id=None, user_ingredients=None, mood_params=None,
                  health_params=None, weights=None, top_k=10):

        # 1. Determinazione automatica dei pesi (Context-Aware)
        if weights is None:
            weights = {
                'alpha_mood':    0.0,
                'beta_content':  0.0,
                'gamma_cf':      0.0,
                'delta_health':  0.0,
                'epsilon_pop':   0.0
            }

            is_cold_start = True
            if user_id is not None:
                user_hist = self.cf_model.df_interactions[
                    self.cf_model.df_interactions['user_id'] == user_id
                ]
                if len(user_hist) >= self.cf_model.min_user_interactions:
                    is_cold_start = False

            if is_cold_start:
                weights['epsilon_pop'] = 1.0
                if mood_params:
                    weights['epsilon_pop'] = 0.4
                    weights['alpha_mood']  = 0.6
            else:
                weights['gamma_cf'] = 1.0
                if mood_params:
                    weights['gamma_cf']   = 0.6
                    weights['alpha_mood'] = 0.4

            if user_ingredients:
                for k in weights:
                    weights[k] *= 0.5
                weights['beta_content'] = 0.5

            if health_params and health_params.get('profile_name'):
                for k in weights:
                    weights[k] *= 0.8
                weights['delta_health'] = 0.2

        # Normalizzazione pesi
        total_w = sum(weights.values())
        if total_w > 0:
            weights = {k: v / total_w for k, v in weights.items()}

        print(f"-> Pesi ibridi applicati: "
              f"mood={weights['alpha_mood']:.2f} | "
              f"content={weights['beta_content']:.2f} | "
              f"CF={weights['gamma_cf']:.2f} | "
              f"health={weights['delta_health']:.2f} | "
              f"pop={weights['epsilon_pop']:.2f}")

        # 2. Raccolta punteggi dai sotto-modelli
        pool_size = 200
        scores_mood, scores_content = {}, {}
        scores_cf, scores_health, scores_pop = {}, {}, {}

        pop_res    = self.pop_model.recommend(top_k=pool_size)
        scores_pop = {r['id']: r['score'] for r in pop_res}

        if mood_params and weights['alpha_mood'] > 0:
            mood_res    = self.mood_model.recommend(**mood_params, top_k=pool_size)
            scores_mood = {r['id']: r['distanza_geometrica'] for r in mood_res}

        if user_ingredients and weights['beta_content'] > 0:
            cont_res       = self.content_model.recommend(
                user_ingredients, top_k=pool_size, max_missing_ingredients=3
            )
            scores_content = {r['id']: r['similarity'] for r in cont_res}

        if user_id is not None and weights['gamma_cf'] > 0:
            try:
                cf_res    = self.cf_model.recommend(user_id=user_id, top_k=pool_size)
                scores_cf = {r['id']: r['rating_predetto'] for r in cf_res}
            except ValueError as e:
                print(f"   CF fallback per user {user_id}: {e}")

        if health_params and weights['delta_health'] > 0:
            h_res          = self.health_model.recommend(**health_params, top_k=pool_size)
            scores_health  = {r['id']: r['health_score'] for r in h_res}

        # 3. Normalizzazione in [0, 1]
        norm_pop     = self._minmax_scale_dict(scores_pop)
        norm_mood    = self._minmax_scale_dict(scores_mood, invert=True)
        norm_content = self._minmax_scale_dict(scores_content)
        norm_cf      = self._minmax_scale_dict(scores_cf)
        norm_health  = self._minmax_scale_dict(scores_health)

        # 4. Aggregazione lineare pesata
        all_ids = (set(norm_pop) | set(norm_mood) | set(norm_content) |
                   set(norm_cf) | set(norm_health))

        hybrid_scores = []
        for r_id in all_ids:
            final_score = (
                weights['alpha_mood']   * norm_mood.get(r_id, 0.0) +
                weights['beta_content'] * norm_content.get(r_id, 0.0) +
                weights['gamma_cf']     * norm_cf.get(r_id, 0.0) +
                weights['delta_health'] * norm_health.get(r_id, 0.0) +
                weights['epsilon_pop']  * norm_pop.get(r_id, 0.0)
            )
            hybrid_scores.append((r_id, final_score))

        hybrid_scores = sorted(hybrid_scores, key=lambda x: x[1], reverse=True)[:top_k]

        # 5. Costruzione output con metadati
        output = []
        for r_id, f_score in hybrid_scores:
            recipe_meta = self.pop_model.df_recipes[
                self.pop_model.df_recipes['id'] == r_id
            ]
            if recipe_meta.empty:
                continue
            recipe_meta = recipe_meta.iloc[0]
            output.append({
                'id':                   int(r_id),
                'name':                 recipe_meta['name'],
                'score_ibrido_finale':  round(float(f_score), 4),
                'calorie':              round(float(recipe_meta['calories']), 1),
                'minuti':               int(recipe_meta['minutes'])
            })

        return output

    def explain(self, user_id, recipe_id):
        """Spiega perché una ricetta è stata raccomandata (aggancio per il layer LLM)."""
        result = {'recipe_id': recipe_id}

        ranked = self.pop_model.df_ranked
        if ranked is not None:
            row = ranked[ranked['recipe_id'] == recipe_id]
            if not row.empty:
                result['popularity_score'] = round(float(row.iloc[0]['score']), 4)

        if user_id is not None:
            try:
                pred = self.cf_model.model.predict(uid=user_id, iid=recipe_id)
                result['cf_predicted_rating'] = round(float(pred.est), 2)
            except Exception:
                result['cf_predicted_rating'] = None

        return result