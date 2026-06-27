"""
Pagina 4 — Mood-Based.

L'utente regola sei slider corrispondenti alle dimensioni emotive
descritte nel paper di Ueda et al. (2016): Body, Mental, Taste, Time,
Price, Modification. Il sistema calcola la distanza euclidea tra il
vettore utente e il vettore mood (precalcolato) di ogni ricetta.
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from style import get_css, recipe_card_html, empty_state_html
from data_loader import get_mood_based_model

st.set_page_config(page_title="Mood — Food Recommender", page_icon="🎭", layout="wide")
st.markdown(get_css(), unsafe_allow_html=True)

st.markdown('<p class="eyebrow">Modello 4 — Sei dimensioni emotive</p>', unsafe_allow_html=True)
st.title("Come ti senti oggi?")
st.caption(
    "Sposta gli slider verso il polo che ti rappresenta di più. "
    "Zero significa nessuna preferenza su quella dimensione."
)

model = get_mood_based_model()

# --- Sei slider, due colonne ---
col1, col2 = st.columns(2)

with col1:
    body = st.slider("Body — leggero ↔ di cuore", -5.0, 5.0, 0.0, step=0.5,
                     help="Negativo: vuoi mangiare leggero. Positivo: vuoi mangiare di cuore.")
    taste = st.slider("Taste — delicato ↔ ricco", -5.0, 5.0, 0.0, step=0.5,
                      help="Negativo: sapore delicato. Positivo: sapore intenso e grasso.")
    mental = st.slider("Mental — salutare ↔ confortante", -5.0, 5.0, 0.0, step=0.5,
                       help="Negativo: vuoi sentirti in forma. Positivo: vuoi coccolarti.")

with col2:
    time = st.slider("Time — veloce ↔ elaborato", -5.0, 5.0, 0.0, step=0.5,
                     help="Negativo: hai poco tempo. Positivo: vuoi cucinare con cura.")
    price = st.slider("Price — economico ↔ costoso", -5.0, 5.0, 0.0, step=0.5,
                      help="Negativo: vuoi spendere poco. Positivo: puoi permetterti ingredienti costosi.")
    modification = st.slider("Modification — classico ↔ sperimentale", -5.0, 5.0, 0.0, step=0.5,
                             help="Negativo: vuoi qualcosa di tradizionale. Positivo: vuoi sperimentare.")

top_k = st.number_input("Quante ricette mostrare", min_value=3, max_value=30, value=10, step=1)

st.markdown("---")

results = model.recommend(
    body=body, mental=mental, taste=taste,
    time=time, price=price, modification=modification,
    top_k=int(top_k),
)

if not results:
    st.markdown(
        empty_state_html("Nessuna ricetta trovata. Riprova con valori diversi."),
        unsafe_allow_html=True,
    )
else:
    st.caption(f"{len(results)} ricette più vicine al tuo mood attuale")

    for r in results:
        scores = r["mood_scores"]
        meta = (
            f"{r['minuti']} min · {r['calorie']} kcal · "
            f"body {scores['body']} · time {scores['time']} · taste {scores['taste']}"
        )
        st.markdown(
            recipe_card_html(
                name=r["name"].title(),
                meta=meta,
                score_label="Distanza dal tuo mood",
                score_value=r["distanza_geometrica"],
                highlighted=(r["distanza_geometrica"] < 2.0),
            ),
            unsafe_allow_html=True,
        )