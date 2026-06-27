"""
Caricamento centralizzato di dataset e modelli, con cache Streamlit.

IMPORTANTE: ogni pagina deve importare da qui invece di rifare
pd.read_csv() o model.fit() per conto proprio — altrimenti Streamlit
ricalcola tutto a ogni interazione dell'utente (ogni slider, ogni click).

@st.cache_data    → usato per dati serializzabili (DataFrame)
@st.cache_resource → usato per oggetti complessi (modelli con stato interno)
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd

from config import PATH_CLEAN_RECIPES, PATH_CLEAN_INTERACTIONS
from models.popularity import PopularityRecommender
from models.content_based import ContentBasedRecommender
from models.health_based import HealthBasedRecommender
from models.mood_based import MoodBasedRecommender
from models.collaborative_filtering import CollaborativeFilteringRecommender
from models.hybrid_based import HybridRecommender


@st.cache_data
def load_recipes() -> pd.DataFrame:
    return pd.read_csv(PATH_CLEAN_RECIPES)


@st.cache_data
def load_interactions() -> pd.DataFrame:
    return pd.read_csv(PATH_CLEAN_INTERACTIONS)


@st.cache_resource
def get_popularity_model() -> PopularityRecommender:
    df_recipes = load_recipes()
    df_interactions = load_interactions()
    model = PopularityRecommender(m=50)
    model.fit(df_recipes, df_interactions)
    return model


@st.cache_resource
def get_content_based_model() -> ContentBasedRecommender:
    df_recipes = load_recipes()
    model = ContentBasedRecommender()
    model.fit(df_recipes)
    return model


@st.cache_resource
def get_health_based_model() -> HealthBasedRecommender:
    df_recipes = load_recipes()
    model = HealthBasedRecommender()
    model.fit(df_recipes)
    return model


@st.cache_resource
def get_mood_based_model() -> MoodBasedRecommender:
    df_recipes = load_recipes()
    model = MoodBasedRecommender()
    model.fit(df_recipes)
    return model


@st.cache_resource
def get_collaborative_filtering_model() -> CollaborativeFilteringRecommender:
    df_recipes = load_recipes()
    df_interactions = load_interactions()
    model = CollaborativeFilteringRecommender(min_user_interactions=5)
    model.fit(df_recipes, df_interactions)
    return model


@st.cache_resource
def get_hybrid_model() -> HybridRecommender:
    pop = get_popularity_model()
    content = get_content_based_model()
    health = get_health_based_model()
    mood = get_mood_based_model()
    cf = get_collaborative_filtering_model()
    return HybridRecommender(pop, content, mood, cf, health)


def parse_user_id(raw_value: str):
    """
    Converte l'input testuale dello User ID in un formato utilizzabile
    dai modelli, oppure restituisce None se il campo è vuoto.
    """
    if raw_value is None or raw_value.strip() == "":
        return None
    raw_value = raw_value.strip()
    try:
        return int(raw_value)
    except ValueError:
        return raw_value