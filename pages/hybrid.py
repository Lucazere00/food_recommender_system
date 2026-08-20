"""
Pagina 5 — Hybrid Recommender.

Combina Popularity, Content-based, Mood, Collaborative Filtering e
Health-based con pesi che si adattano automaticamente al contesto:
se l'utente non ha una storia (cold start) il peso si sposta su
popularity e mood; se ha ingredienti, si attiva il content-based;
se ha vincoli nutrizionali, si attiva il layer salutistico.

Lo User ID viene letto dalla sidebar (condiviso con la pagina
Collaborative Filtering, se presente).
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from style import get_css, recipe_card_html, empty_state_html, render_sidebar
from utils.links import build_foodcom_url
from data_loader import get_hybrid_model, parse_user_id

st.set_page_config(
    page_title="Ibrido — Food Recommender",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(get_css(), unsafe_allow_html=True)
render_sidebar(mode="pages")

st.markdown('<p class="eyebrow">Modello 5 — Combinazione context-aware</p>', unsafe_allow_html=True)
st.title("Il sistema completo")
st.caption(
    "Attiva solo i parametri che ti interessano: il modello adatta "
    "automaticamente i pesi in base a cosa hai fornito. Lo User ID si "
    "imposta dalla barra laterale."
)

model = get_hybrid_model()

user_id_raw = st.session_state.get("user_id", "")
user_id = parse_user_id(user_id_raw)

if user_id is not None:
    st.success(f"Stai usando il profilo utente **{user_id}** — se ha abbastanza interazioni, il Collaborative Filtering sarà attivo.")
else:
    st.info("Nessuno User ID impostato — il modello tratterà la richiesta come un nuovo utente (cold start).")

st.markdown("---")

# --- Parametri opzionali raggruppati in tab ---
tab_mood, tab_fridge, tab_health = st.tabs(["🎭 Mood", "🥗 Svuota-Frigo", "🥦 Vincoli salutistici"])

with tab_mood:
    use_mood = st.checkbox("Attiva il mood in questa raccomandazione")
    mood_params = None
    if use_mood:
        c1, c2 = st.columns(2)
        with c1:
            body = st.slider("Body", -5.0, 5.0, 0.0, step=0.5, key="hy_body")
            taste = st.slider("Taste", -5.0, 5.0, 0.0, step=0.5, key="hy_taste")
            mental = st.slider("Mental", -5.0, 5.0, 0.0, step=0.5, key="hy_mental")
        with c2:
            time = st.slider("Time", -5.0, 5.0, 0.0, step=0.5, key="hy_time")
            price = st.slider("Price", -5.0, 5.0, 0.0, step=0.5, key="hy_price")
            modification = st.slider("Modification", -5.0, 5.0, 0.0, step=0.5, key="hy_mod")
        mood_params = {
            "body": body, "mental": mental, "taste": taste,
            "time": time, "price": price, "modification": modification,
        }

with tab_fridge:
    ingredients_raw = st.text_input(
        "Ingredienti disponibili (lascia vuoto per non attivare)",
        placeholder="es. chicken, garlic, lemon",
        key="hy_ingredients",
    )
    user_ingredients = (
        [i.strip() for i in ingredients_raw.split(",") if i.strip()]
        if ingredients_raw.strip() else None
    )

with tab_health:
    use_health = st.checkbox("Attiva i vincoli nutrizionali in questa raccomandazione")
    health_params = None
    if use_health:
        c1, c2 = st.columns(2)
        with c1:
            hy_max_cal = st.slider("Calorie massime", 100, 1500, 600, step=50, key="hy_maxcal")
            hy_profile = st.selectbox(
                "Obiettivo", ["balanced", "weight_loss", "muscle_gain"], key="hy_profile"
            )
        with c2:
            hy_min_prot = st.slider("Proteine minime (% DV)", 0, 100, 20, step=5, key="hy_minprot")
            hy_tags = st.multiselect(
                "Vincoli dietetici",
                ["vegan", "vegetarian", "gluten-free", "dairy-free", "low-sodium"],
                key="hy_tags",
            )
        health_params = {
            "max_calories": hy_max_cal,
            "min_protein_pct": hy_min_prot,
            "tags_required": hy_tags if hy_tags else None,
            "profile_name": hy_profile,
        }

st.markdown("---")

top_k = st.number_input("Quante ricette mostrare", min_value=3, max_value=30, value=10, step=1)
run = st.button("Genera raccomandazioni", type="primary")

if run:
    results = model.recommend(
        user_id=user_id,
        user_ingredients=user_ingredients,
        mood_params=mood_params,
        health_params=health_params,
        top_k=int(top_k),
    )

    if not results:
        st.markdown(
            empty_state_html(
                "Nessuna ricetta trovata con questa combinazione di parametri. "
                "Prova a disattivare uno dei filtri opzionali."
            ),
            unsafe_allow_html=True,
        )
    else:
        st.caption(f"{len(results)} ricette raccomandate")

        for r in results:
            meta = f"{r['minuti']} min · {r['calorie']} kcal"
            st.markdown(
                recipe_card_html(
                    name=r["name"].title(),
                    meta=meta,
                    score_label="Score ibrido",
                    score_value=r["score_ibrido_finale"],
                    highlighted=True,
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

        with st.expander("Spiega la prima raccomandazione"):
            explanation = model.explain(user_id, results[0]["id"])
            st.json(explanation)
else:
    st.markdown(
        empty_state_html("Imposta i parametri che vuoi e premi «Genera raccomandazioni»."),
        unsafe_allow_html=True,
    )
