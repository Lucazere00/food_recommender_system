PATH_RAW_RECIPES      = "dataset/RAW_recipes.csv"
PATH_RAW_INTERACTIONS = "dataset/RAW_interactions.csv"
PATH_CLEAN_RECIPES    = "dataset/clean_recipes.csv"
PATH_CLEAN_INTERACTIONS = "dataset/clean_interactions.csv"

MIN_USER_INTERACTIONS = 5     # soglia per collaborative filtering
MIN_RECIPE_RATINGS    = 10    # ricette con meno voti escluse dal CF
TOP_K                 = 10    # numero di raccomandazioni restituite
# Soglia massima di calorie per evitare errori e porzioni da banchetto
MAX_CALORIES = 3500

OPENAI_API_KEY = "sk-..."     # solo se usi LLM — altrimenti lascia vuoto