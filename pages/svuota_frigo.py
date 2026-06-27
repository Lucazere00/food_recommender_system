"""
Pagina 2 — Svuota-Frigo (Content-Based).

L'utente inserisce gli ingredienti disponibili. Il sistema vettorizza
gli ingredienti con TF-IDF e calcola la cosine similarity per trovare
le ricette più compatibili, mostrando quali ingredienti l'utente ha
già e quali gli mancherebbero.
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from style import get_css, recipe_card_html, empty_state_html
from data_loader import get_content_based_model

st.set_page_config(page_title="Svuota-Frigo — Food Recommender", page_icon="🥗", layout="wide")
st.markdown(get_css(), unsafe_allow_html=True)

st.markdown('<p class="eyebrow">Modello 2 — Content-based su ingredienti</p>', unsafe_allow_html=True)
st.title("Cosa hai in frigo?")
st.caption(
    "Scrivi gli ingredienti che hai disponibili, separati da virgola. "
    "Il sistema confronta il loro vettore TF-IDF con quello di ogni "
    "ricetta per trovare le corrispondenze migliori."
)

model = get_content_based_model()

# --- Input utente ---
ingredients_raw = st.text_input(
    "Ingredienti disponibili",
    placeholder="es. chicken breast, lemon, rosemary, garlic",
    help="In inglese per maggiore precisione, dato che il dataset è in inglese.",
)

col1, col2 = st.columns(2)
with col1:
    max_missing = st.slider(
        "Massimo numero di ingredienti extra richiesti",
        min_value=0, max_value=6, value=2,
        help="0 significa: la ricetta deve usare SOLO ciò che hai indicato.",
    )
with col2:
    top_k = st.number_input("Quante ricette mostrare", min_value=3, max_value=30, value=10, step=1)

st.markdown("---")

if not ingredients_raw.strip():
    st.markdown(
        empty_state_html(
            "Inserisci almeno un ingrediente per vedere le ricette compatibili."
        ),
        unsafe_allow_html=True,
    )
else:
    ingredients_list = [i.strip() for i in ingredients_raw.split(",") if i.strip()]

    st.caption("Stai cercando ricette con: " + ", ".join(f"**{i}**" for i in ingredients_list))

    results = model.recommend(
        ingredients_list,
        max_missing_ingredients=int(max_missing),
        top_k=int(top_k),
    )

    if not results:
        st.markdown(
            empty_state_html(
                "Nessuna ricetta trovata con questi ingredienti e questo vincolo. "
                "Prova ad aumentare il numero massimo di ingredienti extra, "
                "oppure controlla che gli ingredienti siano scritti in inglese."
            ),
            unsafe_allow_html=True,
        )
    else:
        st.caption(f"{len(results)} ricette trovate")

        for r in results:
            meta = f"{r['minuti']} min · {r['calorie']} kcal"
            st.markdown(
                recipe_card_html(
                    name=r["name"].title(),
                    meta=meta,
                    score_label="Similarità",
                    score_value=r["similarity"],
                    pills_have=r["ingredienti_trovati"],
                    pills_missing=r["ingredienti_mancanti"],
                    highlighted=(len(r["ingredienti_mancanti"]) == 0),
                ),
                unsafe_allow_html=True,
            )