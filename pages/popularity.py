"""
Pagina 1 — Popularity Baseline.

Nessun profilo utente richiesto. Mostra le ricette più apprezzate
dalla community, opzionalmente filtrate per tag, usando la Bayesian
Average per bilanciare rating medio e numero di voti.
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from style import get_css, recipe_card_html, empty_state_html, render_sidebar
from data_loader import get_popularity_model

st.set_page_config(
    page_title="Popularity — Food Recommender",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(get_css(), unsafe_allow_html=True)
render_sidebar(mode="pages")

st.markdown('<p class="eyebrow">Modello 1 — Nessun login richiesto</p>', unsafe_allow_html=True)
st.title("Le ricette più apprezzate")
st.caption(
    "Punteggio calcolato con Bayesian Average: bilancia il rating medio "
    "con il numero di voti, così una ricetta con un solo 5 stelle non "
    "batte una con migliaia di recensioni solide."
)

model = get_popularity_model()

# --- Filtri ---
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    tag_input = st.text_input(
        "Filtra per tag (opzionale)",
        placeholder="es. low-carb, dessert, vegan, italian...",
        help="Inserisci esattamente un tag come compare nel dataset Food.com.",
    )

with col2:
    st.markdown("&nbsp;")  # spaziatura verticale per alineare i bottoni
    sort_label = st.selectbox(
        "Ordina per",
        ["Score bayesiano", "Rating medio", "Numero di voti"],
    )

with col3:
    top_k = st.number_input("Quante ricette", min_value=3, max_value=30, value=10, step=1)

st.markdown("---")

# --- Esecuzione raccomandazione ---
tag_clean = tag_input.strip() if tag_input.strip() else None
results = model.recommend(tag=tag_clean, top_k=int(top_k))

sort_key_map = {
    "Score bayesiano": "score",
    "Rating medio": "rating_medio",
    "Numero di voti": "numero_voti",
}
sort_key = sort_key_map[sort_label]
results = sorted(results, key=lambda r: r[sort_key], reverse=True)

if not results:
    st.markdown(
        empty_state_html(
            f"Nessuna ricetta trovata con il tag «{tag_clean}». "
            "Controlla l'ortografia o provane un altro."
        ),
        unsafe_allow_html=True,
    )
else:
    st.caption(f"{len(results)} ricette trovate" + (f" con il tag «{tag_clean}»" if tag_clean else ""))

    for r in results:
        meta = f"{r['minuti']} min · {r['calorie']} kcal · {r['numero_voti']} voti"
        st.markdown(
            recipe_card_html(
                name=r["name"].title(),
                meta=meta,
                score_label="Rating medio " + str(r["rating_medio"]),
                score_value=f"score {r['score']}",
            ),
            unsafe_allow_html=True,
        )
