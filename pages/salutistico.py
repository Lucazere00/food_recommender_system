"""
Pagina 3 — Recommender Salutistico (Constraint-Based).

Combina vincoli rigidi (calorie massime, proteine minime, tag dietetici)
con uno scoring soft personalizzato per obiettivo (weight_loss,
muscle_gain, balanced). Include anche la generazione di un piano
settimanale di 7 giorni senza ripetizioni.
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from style import get_css, recipe_card_html, empty_state_html
from data_loader import get_health_based_model

st.set_page_config(page_title="Salutistico — Food Recommender", page_icon="🥦", layout="wide")
st.markdown(get_css(), unsafe_allow_html=True)

st.markdown('<p class="eyebrow">Modello 3 — Constraint-based nutrizionale</p>', unsafe_allow_html=True)
st.title("Obiettivi nutrizionali")
st.caption(
    "I valori percentuali (proteine, grassi, sodio) sono espressi come "
    "% Daily Value su una dieta da 2000 kcal, coerentemente col dataset "
    "Food.com. Le calorie sono invece valori assoluti in kcal."
)

model = get_health_based_model()

# --- Vincoli ---
col1, col2 = st.columns(2)

with col1:
    max_calories = st.slider("Calorie massime per porzione", 100, 1500, 600, step=50)
    profile_name = st.selectbox(
        "Obiettivo",
        ["balanced", "weight_loss", "muscle_gain"],
        format_func=lambda x: {
            "balanced": "Bilanciato",
            "weight_loss": "Perdita di peso",
            "muscle_gain": "Aumento massa",
        }[x],
    )

with col2:
    min_protein = st.slider("Proteine minime (% Daily Value)", 0, 100, 20, step=5)
    diet_tags = st.multiselect(
        "Vincoli dietetici",
        ["vegan", "vegetarian", "gluten-free", "dairy-free", "low-sodium"],
    )

tab1, tab2 = st.tabs(["Singola ricetta", "Piano settimanale"])

# ---------------------------------------------------------------------------
# TAB 1 — Raccomandazione singola
# ---------------------------------------------------------------------------
with tab1:
    top_k = st.number_input("Quante ricette mostrare", min_value=3, max_value=30, value=10, step=1, key="hb_topk")

    results = model.recommend(
        max_calories=max_calories,
        min_protein_pct=min_protein,
        tags_required=diet_tags if diet_tags else None,
        profile_name=profile_name,
        top_k=int(top_k),
    )

    if not results:
        st.markdown(
            empty_state_html(
                "Nessuna ricetta rispetta tutti questi vincoli contemporaneamente. "
                "Prova ad alzare le calorie massime o a rimuovere un vincolo dietetico."
            ),
            unsafe_allow_html=True,
        )
    else:
        st.caption(f"{len(results)} ricette trovate")
        for r in results:
            meta = f"{r['minuti']} min · {r['calories']} kcal · proteine {r['protein_pdv']}% DV · grassi {r['fat_pdv']}% DV"
            st.markdown(
                recipe_card_html(
                    name=r["name"].title(),
                    meta=meta,
                    score_label="Health score",
                    score_value=r["health_score"],
                ),
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------------------------
# TAB 2 — Piano settimanale
# ---------------------------------------------------------------------------
with tab2:
    st.caption(
        "Genera un piano di 7 giorni campionando senza ripetizioni dalle "
        "ricette migliori secondo i vincoli impostati sopra."
    )

    if st.button("Genera piano settimanale", type="primary"):
        try:
            plan = model.generate_weekly_plan(
                max_calories=max_calories,
                min_protein_pct=min_protein,
                tags_required=diet_tags if diet_tags else None,
                profile_name=profile_name,
                days=7,
            )
            st.session_state["weekly_plan"] = plan
        except ValueError as e:
            st.session_state["weekly_plan"] = None
            st.markdown(empty_state_html(str(e)), unsafe_allow_html=True)

    plan = st.session_state.get("weekly_plan")
    if plan:
        cols = st.columns(7)
        for col, (day, recipe) in zip(cols, plan.items()):
            with col:
                st.markdown(f"**{day}**")
                st.markdown(
                    recipe_card_html(
                        name=recipe["name"].title()[:30],
                        meta=f"{recipe['calories']} kcal",
                        score_label="Score",
                        score_value=recipe["health_score"],
                    ),
                    unsafe_allow_html=True,
                )