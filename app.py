"""Home page del Food Recommender System."""

import streamlit as st

from data_loader import get_hybrid_model
from page_views import PAGE_RENDERERS
from style import get_css, render_sidebar


st.set_page_config(
    page_title="Food Recommender",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(get_css(), unsafe_allow_html=True)
get_hybrid_model()

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "home"

render_sidebar(mode="internal")

current_page = st.session_state.get("current_page", "home")
PAGE_RENDERERS.get(current_page, PAGE_RENDERERS["home"])()
