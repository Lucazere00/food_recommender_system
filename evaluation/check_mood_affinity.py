import os
import sys

import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import PATH_CLEAN_RECIPES
from models.mood_based import MoodBasedRecommender


def main(sample_size=50):
    df_recipes = pd.read_csv(PATH_CLEAN_RECIPES)
    model = MoodBasedRecommender()
    model.fit(df_recipes)

    results = model.recommend(top_k=sample_size)
    affinity_values = [r["affinita_pct"] for r in results]

    assert affinity_values, "Nessuna ricetta restituita dal recommender."
    assert all(0 <= value <= 100 for value in affinity_values), (
        "affinita_pct fuori range [0, 100]: "
        f"{affinity_values}"
    )

    print(
        "OK: affinita_pct in [0, 100] per "
        f"{len(affinity_values)} ricette "
        f"(min={min(affinity_values)}, max={max(affinity_values)})."
    )


if __name__ == "__main__":
    main()
