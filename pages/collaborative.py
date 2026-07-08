"""
Pagina 5 — Collaborative Filtering (SVD).

L'utente inserisce il proprio User ID (impostato dalla sidebar). Il
sistema usa l'algoritmo SVD addestrato su Surprise per predire il
rating che l'utente darebbe a ricette non ancora viste. Se l'utente
è in cold start (meno di 5 interazioni nel dataset), il sistema
ricade automaticamente sul modello di Popularity.
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from style import get_css, recipe_card_html, empty_state_html, render_sidebar
from data_loader import get_collaborative_filtering_model, get_popularity_model, parse_user_id

st.set_page_config(
    page_title="Collaborative — Food Recommender",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(get_css(), unsafe_allow_html=True)
render_sidebar(mode="pages")

st.markdown('<p class="eyebrow">Modello 5 — Filtro collaborativo (SVD)</p>', unsafe_allow_html=True)
st.title("Raccomandazioni basate sulla community")
st.caption(
    "Usa l'algoritmo SVD addestrato sulle interazioni storiche per "
    "predire quanto ti piacerebbe una ricetta che non hai ancora "
    "provato. Serve uno User ID con almeno 5 interazioni nel dataset; "
    "altrimenti il sistema mostra le ricette più popolari."
)

cf_model = get_collaborative_filtering_model()
pop_model = get_popularity_model()

user_id_raw = st.session_state.get("user_id", "")
user_id = parse_user_id(user_id_raw)

top_k = st.number_input("Quante ricette mostrare", min_value=3, max_value=30, value=10, step=1)

st.markdown("---")

if user_id is None:
    st.markdown(
        empty_state_html(
            "Inserisci uno User ID nella barra laterale per ricevere "
            "raccomandazioni personalizzate. Senza ID il sistema non sa "
            "quale cronologia usare."
        ),
        unsafe_allow_html=True,
    )
else:
    user_history = cf_model.df_interactions[
        cf_model.df_interactions["user_id"] == user_id
    ]

    if len(user_history) < cf_model.min_user_interactions:
        st.info(
            f"L'utente **{user_id}** ha solo {len(user_history)} interazioni "
            f"nel dataset (minimo richiesto: {cf_model.min_user_interactions}). "
            "Mostro le ricette più popolari come fallback."
        )
    else:
        st.success(
            f"Trovate {len(user_history)} interazioni storiche per l'utente "
            f"**{user_id}**. Generazione predizioni SVD in corso..."
        )

    results = cf_model.recommend(
        user_id=user_id,
        top_k=int(top_k),
        popularity_fallback_model=pop_model,
    )

    if not results:
        st.markdown(
            empty_state_html("Nessuna raccomandazione disponibile per questo utente."),
            unsafe_allow_html=True,
        )
    else:
        st.caption(f"{len(results)} ricette raccomandate")

        for r in results:
            meta = f"{r['minuti']} min · {r['calorie']} kcal"
            if "rating_predetto" in r:
                score_label = "Rating predetto"
                score_value = f"{r['rating_predetto']} ⭐"
            else:
                score_label = "Score popolarità"
                score_value = r["score"]

            st.markdown(
                recipe_card_html(
                    name=r["name"].title(),
                    meta=meta,
                    score_label=score_label,
                    score_value=score_value,
                    highlighted=("rating_predetto" in r and r["rating_predetto"] >= 4.5),
                ),
                unsafe_allow_html=True,
            )
