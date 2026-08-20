import pandas as pd
from models.hybrid_based import HybridRecommender


class DummyModel:
    def __init__(self, df_recipes, ranked=None):
        self.df_recipes = df_recipes
        self.df_ranked = ranked

    def recommend(self, *args, **kwargs):
        # return top-k style list from df_recipes
        rows = []
        for _, r in self.df_recipes.iterrows():
            rows.append({
                "id": int(r["id"]),
                "name": r["name"],
                "score": float(r.get("score", 0.0)),
            })
        return rows


class DummyCF:
    def __init__(self):
        self.df_interactions = pd.DataFrame([])
        self.min_user_interactions = 1000


def test_is_non_food_detects_pan_release():
    dummy = HybridRecommender(None, None, None, None, None)
    meta = {"name": "Pan Release Professional Pan Coating Better Than Pam Spray", "minutes": 1, "calories": 10}
    assert dummy._is_non_food(meta) is True


def test_recommend_excludes_non_food_and_applies_ingredient_filter():
    # Prepare recipes: id=1 is pan release, id=2 is a fish dish
    df = pd.DataFrame([
        {"id": 1, "name": "Pan Release Professional Pan Coating Better Than Pam Spray", "minutes": 1, "calories": 10, "ingredients": ["chemical spray"], "tags": []},
        {"id": 2, "name": "Quick Grilled Fish", "minutes": 10, "calories": 300, "ingredients": ["fish", "salt"], "tags": []},
    ])

    pop = DummyModel(df)
    content = DummyModel(df)
    mood = DummyModel(df)
    cf = DummyCF()
    health = DummyModel(df)

    hybrid = HybridRecommender(pop, content, mood, cf, health)

    results = hybrid.recommend(user_id=None, user_ingredients=["fish"], mood_params=None, health_params=None, top_k=5)
    names = [r["name"] for r in results]
    # ensure pan release not returned
    assert not any("pan release" in n.lower() for n in names)
    # ensure fish recipe is present
    assert any("fish" in n.lower() for n in names)
