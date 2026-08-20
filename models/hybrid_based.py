import os
import sys
import logging
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
        self.logger = logging.getLogger("food_recommender.hybrid")

    @staticmethod
    def _is_non_food(recipe_meta) -> bool:
        """Heuristica per identificare item non-food (spray, coating, mix industriale).

        Basata su pattern nel nome e su outlier calories/minutes.
        """
        if recipe_meta is None:
            return False
        name = str(recipe_meta.get("name", "")).lower()
        minutes = float(recipe_meta.get("minutes") or recipe_meta.get("minutes", 0) or 0)
        calories = float(recipe_meta.get("calories") or recipe_meta.get("calories", 0) or 0)

        # name-based patterns
        non_food_keywords = (
            "spray", "coating", "pan release", "release", "non-stick",
            "seasoning mix", "seasoning", "condiment base", "condiment",
            "bottle", "pack", "can", "aerosol"
        )
        if any(kw in name for kw in non_food_keywords):
            return True

        # statistical outliers: pochissimi minuti ma calorie enormi, oppure calorie praticamente nulle
        try:
            if minutes <= 5 and (calories > 1000 or calories < 5):
                return True
        except Exception:
            pass

        return False

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

        has_hard_health_constraints = bool(health_params) and any(
            health_params.get(k) is not None
            for k in ("max_calories", "min_protein_pct", "tags_required")
        )

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

            if health_params and (
                health_params.get('profile_name') or has_hard_health_constraints
            ):
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

        if health_params and (weights['delta_health'] > 0 or has_hard_health_constraints):
            health_call_params = health_params.copy()
            if not health_call_params.get('profile_name'):
                health_call_params['profile_name'] = 'balanced'
            h_res          = self.health_model.recommend(**health_call_params, top_k=pool_size)
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

        # Filter out non-food / product-like items early
        cleaned_ids = set()
        for r_id in all_ids:
            try:
                recipe_meta = self.pop_model.df_recipes[self.pop_model.df_recipes['id'] == r_id]
                if recipe_meta.empty:
                    continue
                recipe_meta = recipe_meta.iloc[0]
                if self._is_non_food(recipe_meta):
                    self.logger.warning("Escludo item non-food dal pool: %s (%s)", r_id, recipe_meta.get('name'))
                    continue
                cleaned_ids.add(r_id)
            except Exception:
                cleaned_ids.add(r_id)
        all_ids = cleaned_ids

        # If user requested specific ingredients, apply a hard filter: remove
        # recipes that do not contain any of the requested ingredients.
        ingredient_filter_failed = False
        if user_ingredients:
            requested = [str(i).lower() for i in (user_ingredients or [])]
            ids_with_ingredient = set()
            for r_id in all_ids:
                row = self.pop_model.df_recipes[self.pop_model.df_recipes['id'] == r_id]
                if row.empty:
                    continue
                row = row.iloc[0]
                ings = row.get('ingredients') or []
                # normalize ingredient strings
                normalized_ings = [str(i).lower() for i in (ings if isinstance(ings, (list, tuple)) else [ings])]
                if any(any(req in ing for ing in normalized_ings) for req in requested):
                    ids_with_ingredient.add(r_id)

            if ids_with_ingredient:
                all_ids = all_ids & ids_with_ingredient
            else:
                # Hard filter resulted empty: record failure and proceed without
                # silently substituting — downstream we will mark ingredient_match=False
                ingredient_filter_failed = True

        if has_hard_health_constraints:
            eligible_ids = self.health_model.get_eligible_ids(
                max_calories=health_params.get('max_calories'),
                min_protein_pct=health_params.get('min_protein_pct'),
                tags_required=health_params.get('tags_required'),
            )
            all_ids = all_ids & eligible_ids
            if not all_ids:
                if not eligible_ids:
                    print("Nessuna ricetta trovata con i vincoli specificati.")
                    return []
                print("   Nessuna ricetta rispetta i vincoli nutrizionali rigidi "
                      "insieme agli altri criteri; ripiego solo sui vincoli nutrizionali.")
                all_ids = eligible_ids

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

        if os.environ.get("HYBRID_DEBUG") and health_params:
            max_calories = health_params.get('max_calories')
            min_protein_pct = health_params.get('min_protein_pct')
            tags_required = health_params.get('tags_required')

            for recipe in output:
                recipe_id = recipe['id']
                recipe_meta = self.health_model.df_recipes[
                    self.health_model.df_recipes['id'] == recipe_id
                ]
                if recipe_meta.empty:
                    continue
                recipe_meta = recipe_meta.iloc[0]

                if (max_calories is not None and
                        float(recipe_meta['calories']) > max_calories):
                    print(
                        f"HYBRID_DEBUG warning: ricetta {recipe_id} supera "
                        f"max_calories={max_calories}."
                    )

                if (min_protein_pct is not None and
                        float(recipe_meta['protein_pct']) < min_protein_pct):
                    print(
                        f"HYBRID_DEBUG warning: ricetta {recipe_id} sotto "
                        f"min_protein_pct={min_protein_pct}."
                    )

                if tags_required:
                    recipe_tags = [t.lower() for t in recipe_meta['tags']]
                    missing_tags = [
                        tag for tag in tags_required
                        if tag.lower().strip() not in recipe_tags
                    ]
                    if missing_tags:
                        print(
                            f"HYBRID_DEBUG warning: ricetta {recipe_id} senza "
                            f"tag richiesti {missing_tags}."
                        )

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
