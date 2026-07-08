"""
Pagina 1 — Popularity Baseline.

Nessun profilo utente richiesto. Mostra le ricette più apprezzate
dalla community, opzionalmente filtrate per tag, usando la Bayesian
Average per bilanciare rating medio e numero di voti.
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
    popularity_page_css,
    ingredient_pills_html,
)
from data_loader import get_popularity_model, get_top_tags


def format_popularity_rows(df):
    """Converte le righe del ranking nello stesso formato di model.recommend()."""
    output = []
    for _, row in df.iterrows():
        output.append(
            {
                "id": int(row["recipe_id"]),
                "name": row["name"],
                "score": round(float(row["score"]), 4),
                "rating_medio": round(float(row["R"]), 2),
                "numero_voti": int(row["v"]),
                "minuti": int(row["minutes"]),
                "calorie": round(float(row["calories"]), 1),
            }
        )
    return output


def filter_ranked_by_tags(df_ranked, selected_tags):
    """Applica il filtro AND: la ricetta deve contenere tutti i tag scelti."""
    selected_tags_clean = {tag.lower().strip() for tag in selected_tags}
    return df_ranked[
        df_ranked["tags"].apply(
            lambda tags_list: selected_tags_clean.issubset(
                {str(tag).lower().strip() for tag in tags_list}
            )
        )
    ].copy()


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
    page_title="Popularity — Food Recommender",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(get_css(), unsafe_allow_html=True)
st.markdown(popularity_page_css(), unsafe_allow_html=True)
render_sidebar(mode="pages")

st.markdown('<p class="eyebrow">Modello 1 — Nessun login richiesto</p>', unsafe_allow_html=True)
st.title("Le ricette più apprezzate")
st.caption(
    "Punteggio calcolato con Bayesian Average: bilancia il rating medio "
    "con il numero di voti."
)

model = get_popularity_model()
top_tags = get_top_tags()

# --- Filtri ---
col1, col2 = st.columns([2, 1])

with col1:
    selected_tags = st.multiselect(
        "Filtra per tag",
        options=top_tags,
        placeholder="aggiungi un tag...",
        help="150 tag più frequenti, suggeriti mentre scrivi. Le ricette devono contenere tutti i tag scelti.",
        key="popularity_tags",
    )
    st.markdown(
        '<p style="margin-top:-8px; color:var(--muted); font-size:0.82rem; font-weight:500;">'
        "150 tag più frequenti, suggeriti mentre scrivi</p>",
        unsafe_allow_html=True,
    )

with col2:
    top_k = st.number_input("Quante ricette", min_value=3, max_value=30, value=10, step=1)

# --- Esecuzione raccomandazione ---
sort_key = "score"
selected_tags_key = tuple(sorted(tag.lower().strip() for tag in selected_tags))
previous_tags_key = st.session_state.get("popularity_previous_tags")
if previous_tags_key != selected_tags_key:
    st.session_state["popularity_visible_count"] = int(top_k)
    st.session_state["popularity_previous_tags"] = selected_tags_key
elif "popularity_visible_count" not in st.session_state:
    st.session_state["popularity_visible_count"] = int(top_k)

visible_count = int(st.session_state["popularity_visible_count"])
query_top_k = max(30, visible_count + 10)

if len(selected_tags) == 1:
    results = model.recommend(tag=selected_tags[0], top_k=query_top_k)
elif len(selected_tags) > 1:
    cached_tags = st.session_state.get("popularity_cached_tags")
    if cached_tags == selected_tags_key:
        filtered_df = st.session_state.get("popularity_cached_results")
    else:
        filtered_df = filter_ranked_by_tags(model.df_ranked, selected_tags)
        st.session_state["popularity_cached_tags"] = selected_tags_key
        st.session_state["popularity_cached_results"] = filtered_df

    df_sorted = filtered_df.sort_values(
        by="score",
        ascending=False,
    ).head(query_top_k)
    results = format_popularity_rows(df_sorted)
else:
    results = model.recommend(top_k=query_top_k)

if len(selected_tags) <= 1:
    results = sorted(results, key=lambda r: r[sort_key], reverse=True)
visible_results = results[:visible_count]

if not visible_results:
    tags_label = ", ".join(selected_tags) if selected_tags else "i filtri selezionati"
    st.markdown(
        empty_state_html(
            f"Nessuna ricetta trovata con {tags_label}. "
            "Prova a rimuovere un tag o a sceglierne un altro."
        ),
        unsafe_allow_html=True,
    )
else:
    tags_caption = (
        " con i tag selezionati"
        if len(selected_tags) > 1
        else (f" con il tag «{selected_tags[0]}»" if selected_tags else "")
    )
    st.caption(f"{len(visible_results)} ricette trovate{tags_caption}")

    for r in visible_results:
        meta = f"{r['minuti']} min · {r['calorie']} kcal"
        ingredients, steps = get_recipe_details(r["id"])
        vs_average = round(r["rating_medio"] - model.global_mean_rating, 2)
        st.markdown(
            recipe_card_html(
                name=r["name"].title(),
                meta=meta,
                score_label="Rating medio " + str(r["rating_medio"]),
                score_value=f"score {r['score']}",
                votes_badge={"numero_voti": r["numero_voti"]},
                score_separator=" · ",
                ingredients=ingredients,
                steps=steps,
                vs_average=vs_average,
            ),
            unsafe_allow_html=True,
        )

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

    if len(results) > visible_count:
        _, load_more_col, _ = st.columns([1, 1.2, 1])
        with load_more_col:
            if st.button(
                "mostra altre 10 ricette",
                key="popularity_load_more",
                use_container_width=True,
            ):
                st.session_state["popularity_visible_count"] = visible_count + 10
                st.rerun()

    st.markdown(
        """
        <div style="display:flex; gap:22px; align-items:center; flex-wrap:wrap; margin-top:18px; color:var(--soft); font-size:0.85rem;">
            <span><span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#EAF3DE; margin-right:8px;"></span>alta fiducia (200+ voti)</span>
            <span><span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#FAEEDA; margin-right:8px;"></span>media (50-200)</span>
            <span><span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#FCEBEB; margin-right:8px;"></span>bassa (&lt;50)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
