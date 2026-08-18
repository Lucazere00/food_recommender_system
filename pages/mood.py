"""
Pagina 4 — Mood-Based.

L'utente regola sei slider corrispondenti alle dimensioni emotive
descritte nel paper di Ueda et al. (2016): Body, Mental, Taste, Time,
Price, Modification. Il sistema calcola la distanza euclidea tra il
vettore utente e il vettore mood (precalcolato) di ogni ricetta.
"""

import sys
import os
import ast

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from style import (
    get_css,
    recipe_card_html,
    empty_state_html,
    render_sidebar,
    ingredient_pills_html,
)
from data_loader import get_mood_based_model


MOOD_AXES = ["body", "time", "taste", "price", "mental", "modification"]


def render_mood_radar(user_vector: dict, recipe_vector: dict, key: str):
    try:
        import plotly.graph_objects as go
    except ModuleNotFoundError:
        st.caption("Radar mood non disponibile: installa Plotly nel virtualenv.")
        return

    user_values = [user_vector[axis] for axis in MOOD_AXES]
    recipe_values = [recipe_vector[axis] for axis in MOOD_AXES]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=user_values,
        theta=MOOD_AXES,
        fill="toself",
        name="Il tuo mood",
        line=dict(color="#5C7A52", width=2),
        fillcolor="rgba(92, 122, 82, 0.15)",
        opacity=0.85,
    ))
    fig.add_trace(go.Scatterpolar(
        r=recipe_values,
        theta=MOOD_AXES,
        fill="toself",
        name="Questa ricetta",
        line=dict(color="#BF4D2D", width=2),
        fillcolor="rgba(191, 77, 45, 0.15)",
        opacity=0.85,
    ))
    fig.update_layout(
        width=220,
        height=220,
        margin=dict(l=28, r=28, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font=dict(size=10, color="#806F5B"),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                range=[-5, 5],
                tickvals=[-5, 0, 5],
                tickfont=dict(size=9),
                gridcolor="#E2D3B8",
                linecolor="#E2D3B8",
            ),
            angularaxis=dict(
                gridcolor="#E2D3B8",
                linecolor="#E2D3B8",
            ),
        ),
    )
    st.plotly_chart(fig, use_container_width=False, key=key)


def normalize_recipe_list(value):
    """Converte ingredienti o passaggi in una lista Python renderizzabile."""
    if isinstance(value, list):
        return value
    if value is None:
        return []
    try:
        if isinstance(value, str):
            parsed_value = ast.literal_eval(value)
            return parsed_value if isinstance(parsed_value, list) else []
    except (ValueError, SyntaxError):
        return []
    return []


def get_recipe_details(recipe_id):
    """Recupera ingredienti e preparazione solo per la ricetta visualizzata."""
    recipe_row = model.df_recipes.loc[model.df_recipes["id"] == recipe_id]
    if recipe_row.empty:
        return [], []

    recipe = recipe_row.iloc[0]
    ingredients = normalize_recipe_list(recipe.get("ingredients"))
    steps = normalize_recipe_list(recipe.get("steps"))
    return ingredients, steps


st.set_page_config(
    page_title="Mood — Food Recommender",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(get_css(), unsafe_allow_html=True)
render_sidebar(mode="pages")

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
user_vector = {
    "body": body,
    "time": time,
    "taste": taste,
    "price": price,
    "mental": mental,
    "modification": modification,
}

if not results:
    st.markdown(
        empty_state_html("Nessuna ricetta trovata. Riprova con valori diversi."),
        unsafe_allow_html=True,
    )
else:
    st.caption(f"{len(results)} ricette più vicine al tuo mood attuale")

    for i, r in enumerate(results):
        scores = r["mood_scores"]
        ingredients, steps = get_recipe_details(r["id"])
        meta = (
            f"{r['minuti']} min · {r['calorie']} kcal · "
            f"body {scores['body']} · time {scores['time']} · taste {scores['taste']} · "
            f"price {scores['price']} · mental {scores['mental']} · mod {scores['modification']}"
        )
        card_col, radar_col = st.columns([3, 2])
        with card_col:
            st.markdown(
                recipe_card_html(
                    name=r["name"].title(),
                    meta=meta,
                    score_label="Affinità col tuo mood",
                    score_value=f"{int(round(r['affinita_pct']))}%",
                    highlighted=(r["affinita_pct"] > 70),
                    ingredients=ingredients,
                    steps=steps,
                ),
                unsafe_allow_html=True,
            )
        with radar_col:
            render_mood_radar(user_vector, scores, key=f"radar_{r['id']}")

        with st.expander("Vedi ingredienti e preparazione"):
            if not ingredients or not steps:
                st.caption("Dettagli non disponibili per questa ricetta")
            else:
                col_ingredients, col_steps = st.columns(2)
                with col_ingredients:
                    st.markdown(
                        '<p style="margin:0 0 10px; color:var(--soft); font-size:0.78rem; '
                        'font-weight:600; letter-spacing:.08em;">Ingredienti</p>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        ingredient_pills_html(ingredients),
                        unsafe_allow_html=True,
                    )

                with col_steps:
                    st.markdown(
                        '<p style="margin:0 0 10px; color:var(--soft); font-size:0.78rem; '
                        'font-weight:600; letter-spacing:.08em;">Preparazione</p>',
                        unsafe_allow_html=True,
                    )
                    steps_markdown = "\n".join(
                        f"{index}. {step}" for index, step in enumerate(steps, start=1)
                    )
                    st.markdown(steps_markdown)
