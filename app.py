"""Home page del Food Recommender System."""

import streamlit as st

from style import get_css, model_card_html


st.set_page_config(
    page_title="Food Recommender",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(get_css(), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">'
        '<p class="sidebar-title">Food Recommender</p>'
        '<p class="sidebar-subtitle">Tesi — sistemi di raccomandazione</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.page_link("app.py", label="Home")

    st.markdown('<p class="nav-group">Senza profilo</p>', unsafe_allow_html=True)
    st.page_link("pages/popularity.py", label="1 · Popolari")
    st.page_link("pages/svuota_frigo.py", label="2 · Svuota-frigo")

    st.markdown('<p class="nav-group">Con vincoli</p>', unsafe_allow_html=True)
    st.page_link("pages/salutistico.py", label="3 · Salutistico")
    st.page_link("pages/mood.py", label="4 · Mood")

    st.markdown('<p class="nav-group">Personalizzato</p>', unsafe_allow_html=True)
    st.markdown('<p class="nav-placeholder">5 · Collaborative</p>', unsafe_allow_html=True)
    st.page_link("pages/hybrid.py", label="6 · Ibrido")

    st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-user-divider"></div>', unsafe_allow_html=True)

    if "user_id" not in st.session_state:
        st.session_state.user_id = ""

    st.text_input(
        "User ID (opzionale)",
        key="user_id",
        help=(
            "Se inserisci un ID utente presente nel dataset, i modelli "
            "personalizzati useranno la sua cronologia."
        ),
        placeholder="es. 8937",
    )


# ---------------------------------------------------------------------------
# HOME
# ---------------------------------------------------------------------------
st.markdown(
    '<main class="home-shell">'
    '<p class="eyebrow">Tesi — Sistemi di raccomandazione</p>'
    '<h1 class="home-title">Cosa cuciniamo oggi?</h1>'
    '<p class="home-intro">Sei approcci diversi alla raccomandazione di '
    "ricette, costruiti sul dataset Food.com. Scegli da dove iniziare.</p>"
    "</main>",
    unsafe_allow_html=True,
)

st.markdown(
    model_card_html(
        icon="",
        title="Mood-based — dimmi come ti senti",
        description="",
        featured=True,
    ),
    unsafe_allow_html=True,
)

cards = [
    ("Popolari", "Le ricette più votate, pesate con Bayesian Average."),
    ("Svuota-frigo", "Ricette dai tuoi ingredienti disponibili."),
    ("Salutistico", "Vincoli nutrizionali e piano settimanale."),
    ("Collaborative", "SVD sulla cronologia degli utenti."),
    ("Ibrido", "Combina tutti i modelli con pesi adattivi."),
]

cards_html = "".join(
    model_card_html(icon="", title=title, description=description)
    for title, description in cards
)

st.markdown(
    '<div class="model-grid">'
    f"{cards_html}"
    '<div class="model-card model-card-note">'
    "<p>Naviga dalla barra laterale. Ogni modello è indipendente e "
    "testabile da solo.</p>"
    "</div>"
    "</div>",
    unsafe_allow_html=True,
)
