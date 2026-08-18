# config.py
PATH_RAW_RECIPES        = "dataset/RAW_recipes.csv"
PATH_RAW_INTERACTIONS   = "dataset/RAW_interactions.csv"
PATH_CLEAN_RECIPES      = "dataset/clean_recipes.csv"
PATH_CLEAN_INTERACTIONS = "dataset/clean_interactions.csv"
PATH_TFIDF_MATRIX       = "dataset/tfidf_matrix.npz"   # ← mancante
PATH_SAVED_MODELS       = "models/saved/"               # ← mancante

MIN_USER_INTERACTIONS   = 5
MIN_RECIPE_RATINGS      = 10
TOP_K                   = 10
MAX_CALORIES            = 3500

# CF hyperparameters — centralizzati per l'ablation study
SVD_N_FACTORS   = 50
SVD_N_EPOCHS    = 20
SVD_LR_ALL      = 0.005

OPENAI_API_KEY  = ""
GROQ_API_KEY    = "tuo_api_key_qui"
