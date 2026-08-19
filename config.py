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

# NON inserire mai una chiave vera qui: questo file è tracciato da git.
# La chiave va in .streamlit/secrets.toml (ignorato da git) oppure nella
# variabile d'ambiente OPENAI_API_KEY.
OPENAI_API_KEY  = ""
GROQ_API_KEY    = ""
