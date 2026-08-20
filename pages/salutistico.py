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
from style import get_css, recipe_card_html, empty_state_html, render_sidebar
from data_loader import get_health_based_model
from utils.links import build_foodcom_url

st.set_page_config(
    page_title="Salutistico — Food Recommender",
    page_icon="🥦",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(get_css(), unsafe_allow_html=True)
render_sidebar(mode="pages")

st.markdown('<p class="eyebrow">Modello 3 — Constraint-based nutrizionale</p>', unsafe_allow_html=True)
st.title("Obiettivi nutrizionali")
st.caption(
    "I valori percentuali (proteine, grassi, sodio) sono espressi come "
    "% Daily Value su una dieta da 2000 kcal, coerentemente col dataset "
    "Food.com. Le calorie sono invece valori assoluti in kcal."
)

model = get_health_based_model()

PROFILE_LABELS = {
    "balanced": "bilanciato",
    "weight_loss": "perdita di peso",
    "muscle_gain": "aumento massa",
}


def add_goal_compatibility(results):
    """Normalizza gli health_score solo dentro il set mostrato."""
    if not results:
        return results

    scores = [float(r["health_score"]) for r in results]
    min_score = min(scores)
    max_score = max(scores)
    score_range = max_score - min_score

    enriched_results = []
    for recipe in results:
        recipe_with_pct = recipe.copy()
        if score_range == 0:
            compatibility_pct = 100
        else:
            compatibility_pct = round(
                ((float(recipe["health_score"]) - min_score) / score_range) * 100
            )
        recipe_with_pct["goal_compatibility_pct"] = int(compatibility_pct)
        enriched_results.append(recipe_with_pct)

    return enriched_results


def goal_badge_for(compatibility_pct, profile_name):
    profile_label = PROFILE_LABELS[profile_name]
    if compatibility_pct >= 75:
        quality = "ottima"
    elif compatibility_pct >= 40:
        quality = "buona"
    else:
        quality = "scarsa"

    return {
        "label": f"{quality} per {profile_label}",
        "tone": quality,
    }

# --- Vincoli ---
col1, col2 = st.columns(2)

with col1:
    max_calories = st.slider("Calorie massime per porzione", 100, 1500, 250, step=50)
    st.markdown(
        f'<div style="margin-top:-4px; font-size:12px; color:var(--text-muted);">Valore attuale: <strong>{max_calories} kcal</strong></div>',
        unsafe_allow_html=True,
    )
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
    min_protein = st.slider("Proteine minime (% Daily Value)", 0, 100, 35, step=5)
    st.markdown(
        f'<div style="margin-top:-4px; font-size:12px; color:var(--text-muted);">Valore attuale: <strong>{min_protein}% DV</strong></div>',
        unsafe_allow_html=True,
    )
    diet_tags = st.multiselect(
        "Vincoli dietetici",
        ["vegan", "vegetarian", "gluten-free", "dairy-free", "low-sodium"],
        placeholder="Seleziona vincoli (opzionale)",
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

    results = add_goal_compatibility(results)

    if not results:
        st.markdown(
            empty_state_html(
                "Nessuna ricetta rispetta tutti questi vincoli contemporaneamente. "
                "Prova ad alzare le calorie massime o a rimuovere un vincolo dietetico."
            ),
            unsafe_allow_html=True,
        )
    else:
        sort_by = st.selectbox(
            "Ordina per",
            ["Compatibilità con l'obiettivo", "Calorie", "Proteine"],
            index=0,
        )
        if sort_by == "Compatibilità con l'obiettivo":
            results = sorted(
                results,
                key=lambda r: r.get("goal_compatibility_pct", 0),
                reverse=True,
            )
        elif sort_by == "Calorie":
            results = sorted(
                results,
                key=lambda r: float(r.get("calories", 0)),
                reverse=False,
            )
        else:
            results = sorted(
                results,
                key=lambda r: float(r.get("protein_pdv", 0)),
                reverse=True,
            )

        st.caption(f"{len(results)} ricette trovate")
        for r in results:
            meta = f"{r['minuti']} min · {r['calories']} kcal"
            badge_info = goal_badge_for(r["goal_compatibility_pct"], profile_name)
            st.markdown(
                recipe_card_html(
                    name=r["name"].title(),
                    meta=meta,
                    score_label="Compatibilità con l'obiettivo",
                    score_value=f"{r['goal_compatibility_pct']}%",
                    score_separator=": ",
                    compat_pct=float(r["goal_compatibility_pct"]),
                    compat_label=badge_info["label"],
                    protein_pdv=r["protein_pdv"],
                    fat_pdv=r["fat_pdv"],
                ),
                unsafe_allow_html=True,
            )
            try:
                url = build_foodcom_url(r)
            except Exception:
                url = "https://www.food.com/"
            st.markdown(
                f'<a href="{url}" target="_blank" rel="noopener" '
                f'style="font-size:13px; color: var(--text-accent);">'
                f'<i class="ti ti-external-link"></i> Vedi su Food.com</a>',
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
                        try:
                            url = build_foodcom_url(recipe)
                        except Exception:
                            url = "https://www.food.com/"
                        st.markdown(
                            f'<a href="{url}" target="_blank" rel="noopener" '
                            f'style="font-size:13px; color: var(--text-accent);">'
                            f'<i class="ti ti-external-link"></i> Vedi su Food.com</a>',
                            unsafe_allow_html=True,
                        )
