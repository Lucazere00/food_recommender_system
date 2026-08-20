"""
Pagina 2 — Svuota-Frigo (Content-Based).

L'utente inserisce gli ingredienti disponibili. Il sistema vettorizza
gli ingredienti con TF-IDF e calcola la cosine similarity per trovare
le ricette più compatibili, mostrando quali ingredienti l'utente ha
già e quali gli mancherebbero.
"""

import sys
import os
import inspect
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
from data_loader import get_content_based_model, get_common_ingredients
from utils.links import build_foodcom_url


PANTRY_INGREDIENTS = ["salt", "olive oil", "onion", "black pepper", "butter", "garlic"]


def add_pantry_ingredient(ingredient):
    """Aggiunge un ingrediente comune senza duplicarlo."""
    current_ingredients = list(st.session_state.get("fridge_ingredients", []))
    current_normalized = {item.lower().strip() for item in current_ingredients}
    if ingredient.lower().strip() not in current_normalized:
        st.session_state["fridge_ingredients"] = current_ingredients + [ingredient]
        st.rerun()


def calculate_match_pct(found, missing):
    """Calcola la percentuale di ingredienti coperti dalla ricetta."""
    total = len(found) + len(missing)
    if total == 0:
        return 0
    return round((len(found) / total) * 100)


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
    page_title="Svuota-Frigo — Food Recommender",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(get_css(), unsafe_allow_html=True)
render_sidebar(mode="pages")

st.markdown('<p class="eyebrow">Modello 2 — Content-based su ingredienti</p>', unsafe_allow_html=True)
st.title("Cosa hai in frigo?")
st.caption(
    "Scrivi o seleziona gli ingredienti disponibili. Il sistema confronta "
    "il loro vettore TF-IDF con quello di ogni ricetta."
)

model = get_content_based_model()
common_ingredients = get_common_ingredients(model.df_recipes)

# --- Input utente ---
if "fridge_ingredients" not in st.session_state:
    st.session_state["fridge_ingredients"] = []

ingredient_options = list(
    dict.fromkeys(
        list(st.session_state["fridge_ingredients"])
        + PANTRY_INGREDIENTS
        + common_ingredients
    )
)
multiselect_kwargs = {
    "label": "Ingredienti disponibili",
    "options": ingredient_options,
    "placeholder": "aggiungi un ingrediente...",
    "help": "In inglese per maggiore precisione, dato che il dataset è in inglese.",
    "key": "fridge_ingredients",
}
if "accept_new_options" in inspect.signature(st.multiselect).parameters:
    multiselect_kwargs["accept_new_options"] = True

ingredients_list = st.multiselect(**multiselect_kwargs)

st.markdown(
    '<p style="margin:10px 0 8px; color:var(--soft); font-size:0.82rem; '
    'font-weight:600;">Ingredienti comuni — aggiungi in un click</p>',
    unsafe_allow_html=True,
)
pantry_cols = st.columns(len(PANTRY_INGREDIENTS))
for pantry_col, pantry_ingredient in zip(pantry_cols, PANTRY_INGREDIENTS):
    with pantry_col:
        st.button(
            f"+ {pantry_ingredient}",
            key=f"pantry_{pantry_ingredient}",
            on_click=add_pantry_ingredient,
            args=(pantry_ingredient,),
            use_container_width=True,
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

if not ingredients_list:
    st.markdown(
        empty_state_html(
            "Inserisci almeno un ingrediente per vedere le ricette compatibili."
        ),
        unsafe_allow_html=True,
    )
else:
    st.caption("Stai cercando ricette con: " + ", ".join(f"**{i}**" for i in ingredients_list))

    filter_key = (
        tuple(sorted(ingredient.lower().strip() for ingredient in ingredients_list)),
        int(max_missing),
    )
    previous_filter_key = st.session_state.get("fridge_previous_filter")
    if previous_filter_key != filter_key:
        st.session_state["fridge_visible_count"] = int(top_k)
        st.session_state["fridge_previous_filter"] = filter_key
    elif "fridge_visible_count" not in st.session_state:
        st.session_state["fridge_visible_count"] = int(top_k)

    visible_count = int(st.session_state["fridge_visible_count"])
    query_top_k = max(30, visible_count + 10)

    results = model.recommend(
        ingredients_list,
        max_missing_ingredients=int(max_missing),
        top_k=query_top_k,
    )
    visible_results = results[:visible_count]

    if not visible_results:
        st.markdown(
            empty_state_html(
                "Nessuna ricetta trovata con questi ingredienti e questo vincolo. "
                "Prova ad aumentare il numero massimo di ingredienti extra, "
                "oppure controlla che gli ingredienti siano scritti in inglese."
            ),
            unsafe_allow_html=True,
        )
    else:
        st.caption(f"{len(visible_results)} ricette trovate")

        for r in visible_results:
            meta = f"{r['minuti']} min · {r['calorie']} kcal"
            found_ingredients = r["ingredienti_trovati"]
            missing_ingredients = r["ingredienti_mancanti"]
            match_pct = calculate_match_pct(found_ingredients, missing_ingredients)
            is_ready = len(missing_ingredients) == 0
            recipe_ingredients, recipe_steps = get_recipe_details(r["id"])
            st.markdown(
                recipe_card_html(
                    name=r["name"].title(),
                    meta=meta,
                    score_label="Similarità",
                    score_value=r["similarity"],
                    pills_have=found_ingredients,
                    pills_missing=missing_ingredients,
                    highlighted=is_ready,
                    match_pct=match_pct,
                    ready_badge=is_ready,
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

            with st.expander("Vedi ingredienti e preparazione"):
                if not recipe_ingredients or not recipe_steps:
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
                            ingredient_pills_html(recipe_ingredients),
                            unsafe_allow_html=True,
                        )

                    with col_steps:
                        st.markdown(
                            '<p style="margin:0 0 10px; color:var(--soft); font-size:0.78rem; '
                            'font-weight:600; letter-spacing:.08em;">Preparazione</p>',
                            unsafe_allow_html=True,
                        )
                        steps_markdown = "\n".join(
                            f"{index}. {step}"
                            for index, step in enumerate(recipe_steps, start=1)
                        )
                        st.markdown(steps_markdown)

        if len(results) > visible_count:
            _, load_more_col, _ = st.columns([1, 1.2, 1])
            with load_more_col:
                if st.button(
                    "mostra altre 10 ricette",
                    key="fridge_load_more",
                    use_container_width=True,
                ):
                    st.session_state["fridge_visible_count"] = visible_count + 10
                    st.rerun()
