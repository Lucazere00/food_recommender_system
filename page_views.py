"""Viste riusabili per l'app Food Recommender."""

import ast
import inspect

import streamlit as st

from data_loader import (
    get_collaborative_filtering_model,
    get_common_ingredients,
    get_content_based_model,
    get_explainer,
    get_health_based_model,
    get_hybrid_model,
    get_intent_parser,
    get_mood_based_model,
    get_popularity_model,
    get_top_tags,
    parse_user_id,
)
from style import (
    empty_state_html,
    explanation_quote_html,
    ingredient_pills_html,
    param_pills_html,
    popularity_page_css,
    recipe_card_html,
)
from utils.links import build_foodcom_url


PAGE_LABELS = {
    "home": "Home",
    "popularity": "1 · Popolari",
    "svuota_frigo": "2 · Svuota-frigo",
    "salutistico": "3 · Salutistico",
    "mood": "4 · Mood",
    "collaborative": "5 · Collaborative",
    "hybrid": "6 · Ibrido",
}


PANTRY_INGREDIENTS = ["salt", "olive oil", "onion", "black pepper", "butter", "garlic"]
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


def get_recipe_details(model, recipe_id):
    """Recupera ingredienti e preparazione solo per la ricetta visualizzata."""
    df_recipes = getattr(model, "df_recipes", None)
    if df_recipes is None and hasattr(model, "pop_model"):
        df_recipes = getattr(model.pop_model, "df_recipes", None)
    if df_recipes is None:
        return [], []

    recipe_row = df_recipes.loc[df_recipes["id"] == recipe_id]
    if recipe_row.empty:
        return [], []

    recipe = recipe_row.iloc[0]
    ingredients = normalize_recipe_list(recipe.get("ingredients"))
    steps = normalize_recipe_list(recipe.get("steps"))
    return ingredients, steps


def build_home_health_params(intent: dict) -> dict | None:
    health_params = {
        "max_calories": intent.get("max_calories"),
        "min_protein_pct": intent.get("min_protein_pct"),
        "tags_required": intent.get("tags_required"),
        "profile_name": intent.get("profile_name"),
    }
    has_health_signal = any(
        health_params.get(key) not in (None, [], "")
        for key in ("max_calories", "min_protein_pct", "tags_required", "profile_name")
    )
    if not has_health_signal:
        return None
    if not health_params["profile_name"]:
        health_params["profile_name"] = "balanced"
    return health_params


def render_home_llm_results(payload: dict) -> None:
    intent = payload.get("intent", {})
    results = payload.get("results", [])
    explanation = payload.get("explanation")
    health_params = payload.get("health_params")

    st.markdown(
        "<p class=\"eyebrow\">Parametri interpretati</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        param_pills_html(
            mood_dict=intent.get("mood"),
            health_dict=health_params,
            ingredients_list=intent.get("ingredients"),
        ),
        unsafe_allow_html=True,
    )

    if not results:
        st.markdown(
            empty_state_html(
                "Nessuna ricetta trovata con questa richiesta. Prova a togliere "
                "un vincolo o a descrivere ingredienti piu comuni."
            ),
            unsafe_allow_html=True,
        )
        return

    st.caption(f"{len(results)} ricette raccomandate")
    model = get_hybrid_model()
    for index, recipe in enumerate(results):
        meta = f"{recipe['minuti']} min · {recipe['calorie']} kcal"
        ingredients, steps = get_recipe_details(model, recipe["id"])
        st.markdown(
            recipe_card_html(
                name=recipe["name"].title(),
                meta=meta,
                score_label="Score",
                score_value=recipe["score_ibrido_finale"],
                highlighted=index == 0,
            ),
            unsafe_allow_html=True,
        )
        # link esterno a Food.com per la ricetta
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
        if index == 0 and explanation:
            st.markdown(explanation_quote_html(explanation), unsafe_allow_html=True)

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
                        f"{step_index}. {step}" for step_index, step in enumerate(steps, start=1)
                    )
                    st.markdown(steps_markdown)


def render_home() -> None:
    if "home_llm_query" not in st.session_state:
        st.session_state["home_llm_query"] = ""

    st.markdown(
        '<main class="home-shell">'
        '<h1 class="home-title">Cosa cuciniamo oggi?</h1>'
        '<p class="home-intro">Scrivi liberamente: mood, ingredienti disponibili, '
        "vincoli calorici. Il modello capisce e ti propone una ricetta.</p>"
        "</main>",
        unsafe_allow_html=True,
    )

    with st.form("home_llm_form"):
        user_text = st.text_input(
            "Richiesta libera",
            key="home_llm_query",
            label_visibility="collapsed",
            placeholder=(
                "sono stanco dopo lo studio, voglio qualcosa di veloce e "
                "confortante, ho pollo e aglio in frigo, sotto le 500 kcal"
            ),
        )
        submitted = st.form_submit_button(
            "Genera raccomandazione",
            type="primary",
            use_container_width=False,
        )

    if submitted:
        cleaned_text = (user_text or "").strip()
        if not cleaned_text:
            st.warning("Scrivi una richiesta prima di generare la raccomandazione.")
        else:
            parser = get_intent_parser()
            with st.spinner("Il cuoco AI sta pensando..."):
                intent = parser.parse_query(cleaned_text)
                st.session_state["debug_last_error"] = parser.last_error
                health_params = build_home_health_params(intent)
                user_id = parse_user_id(st.session_state.get("user_id", ""))
                model = get_hybrid_model()
                results = model.recommend(
                    user_id=user_id,
                    user_ingredients=intent.get("ingredients"),
                    mood_params=intent.get("mood"),
                    health_params=health_params,
                    top_k=5,
                )

                # Prepare explainer context: fetch ingredients for the top result
                explanation = None
                if results:
                    top_recipe = results[0].copy()
                    ingredients, steps = get_recipe_details(model, top_recipe["id"])
                    top_recipe["ingredients"] = ingredients
                    normalized_ings = [str(i).lower() for i in ingredients] if ingredients else []

                    # Verify excluded ingredients: only pass exclusions if the caller
                    # has already checked and the recipe ingredients are available
                    excluded = intent.get("exclude_ingredients")
                    verified_exclusions = None
                    if excluded and ingredients:
                        # only treat exclusion as verified absent if none of the
                        # excluded canonicals appear in the ingredient strings
                        if not any(e in ing for e in excluded for ing in normalized_ings):
                            verified_exclusions = excluded

                    # ingredient_match: whether any requested ingredient is present
                    requested_ings = intent.get("ingredients") or []
                    ingredient_match = None
                    if requested_ings:
                        ingredient_match = any(
                            any(req in str(ing).lower() for ing in normalized_ings)
                            for req in requested_ings
                        )

                    explanation = get_explainer().generate_explanation(
                        cleaned_text,
                        top_recipe,
                        excluded_ingredients=verified_exclusions,
                        ingredient_match=ingredient_match,
                    )
            st.session_state["home_llm_result"] = {
                "query": cleaned_text,
                "intent": intent,
                "health_params": health_params,
                "results": results,
                "explanation": explanation,
                "llm_configured": parser.is_configured,
                "used_llm_last_call": parser.used_llm_last_call,
                "provider": parser.provider,
                "last_error": parser.last_error,
            }

    home_result = st.session_state.get("home_llm_result")
    if home_result:
        if home_result.get("llm_configured") and not home_result.get("used_llm_last_call"):
            st.warning(
                f"Il provider LLM ha risposto con un errore ({home_result.get('last_error')}); "
                "sto usando il parser locale di riserva, meno preciso sul linguaggio naturale."
            )
        elif not home_result.get("llm_configured"):
            st.warning("Modalita AI non disponibile: nessuna chiave LLM configurata.")
        render_home_llm_results(home_result)
    else:
        st.markdown(
            empty_state_html("Scrivi qualcosa e premi Invio o «Genera raccomandazione»."),
            unsafe_allow_html=True,
        )


def render_popularity() -> None:
    st.markdown(popularity_page_css(), unsafe_allow_html=True)
    
    st.title("Le ricette più apprezzate")
    st.caption(
        "Punteggio calcolato con Bayesian Average: bilancia il rating medio "
        "con il numero di voti."
    )

    model = get_popularity_model()
    top_tags = get_top_tags()

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
        top_k = st.number_input(
            "Quante ricette",
            min_value=3,
            max_value=30,
            value=10,
            step=1,
            key="popularity_top_k",
        )

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
        return

    tags_caption = (
        " con i tag selezionati"
        if len(selected_tags) > 1
        else (f" con il tag «{selected_tags[0]}»" if selected_tags else "")
    )
    st.caption(f"{len(visible_results)} ricette trovate{tags_caption}")

    for r in visible_results:
        meta = f"{r['minuti']} min · {r['calorie']} kcal"
        ingredients, steps = get_recipe_details(model, r["id"])
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


def render_svuota_frigo() -> None:
    
    st.title("Cosa hai in frigo?")
    st.caption(
        "Scrivi o seleziona gli ingredienti disponibili."
        
    )

    model = get_content_based_model()
    common_ingredients = get_common_ingredients(model.df_recipes)

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
            min_value=0,
            max_value=6,
            value=2,
            help="0 significa: la ricetta deve usare SOLO ciò che hai indicato.",
            key="fridge_max_missing",
        )
    with col2:
        top_k = st.number_input(
            "Quante ricette mostrare",
            min_value=3,
            max_value=30,
            value=10,
            step=1,
            key="fridge_top_k",
        )

    st.markdown("---")

    if not ingredients_list:
        st.markdown(
            empty_state_html(
                "Inserisci almeno un ingrediente per vedere le ricette compatibili."
            ),
            unsafe_allow_html=True,
        )
        return

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
        return

    st.caption(f"{len(visible_results)} ricette trovate")
    for r in visible_results:
        meta = f"{r['minuti']} min · {r['calorie']} kcal"
        found_ingredients = r["ingredienti_trovati"]
        missing_ingredients = r["ingredienti_mancanti"]
        match_pct = calculate_match_pct(found_ingredients, missing_ingredients)
        is_ready = len(missing_ingredients) == 0
        recipe_ingredients, recipe_steps = get_recipe_details(model, r["id"])
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


def render_salutistico() -> None:
    
    st.title("Obiettivi nutrizionali")
    st.caption(
        "I valori percentuali (proteine, grassi, sodio) sono espressi come "
        "% Daily Value su una dieta da 2000 kcal, coerentemente col dataset "
        "Food.com. Le calorie sono invece valori assoluti in kcal."
    )

    model = get_health_based_model()

    col1, col2 = st.columns(2)

    with col1:
        max_calories = st.slider(
            "Calorie massime per porzione",
            100,
            1500,
            600,
            step=50,
            key="health_max_calories",
        )
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
            key="health_profile",
        )

    with col2:
        min_protein = st.slider(
            "Proteine minime (% Daily Value)",
            0,
            100,
            20,
            step=5,
            key="health_min_protein",
        )
        st.markdown(
            f'<div style="margin-top:-4px; font-size:12px; color:var(--text-muted);">Valore attuale: <strong>{min_protein}% DV</strong></div>',
            unsafe_allow_html=True,
        )
        diet_tags = st.multiselect(
            "Vincoli dietetici",
            ["vegan", "vegetarian", "gluten-free", "dairy-free", "low-sodium"],
            key="health_diet_tags",
            placeholder="Seleziona vincoli (opzionale)",
        )

    container = st.container()

    with container:
        top_k = st.number_input(
            "Quante ricette mostrare",
            min_value=3,
            max_value=30,
            value=10,
            step=1,
            key="hb_topk",
        )

        health_params_key = (
            float(max_calories),
            float(min_protein),
            tuple(sorted(diet_tags)),
            profile_name,
            int(top_k),
        )
        previous_health_params = st.session_state.get("health_previous_params")
        if previous_health_params != health_params_key:
            st.session_state["health_visible_count"] = int(top_k)
            st.session_state["health_previous_params"] = health_params_key
        elif "health_visible_count" not in st.session_state:
            st.session_state["health_visible_count"] = int(top_k)

        visible_count = int(st.session_state["health_visible_count"])
        query_top_k = max(30, visible_count + 10)

        results = model.recommend(
            max_calories=max_calories,
            min_protein_pct=min_protein,
            tags_required=diet_tags if diet_tags else None,
            profile_name=profile_name,
            top_k=query_top_k,
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

            visible_results = results[:visible_count]

            st.caption(f"{len(visible_results)} ricette trovate")
            for r in visible_results:
                meta = f"{r['minuti']} min · {r['calories']} kcal"
                badge_info = goal_badge_for(r["goal_compatibility_pct"], profile_name)
                ingredients, steps = get_recipe_details(model, r["id"])
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
                        key="health_load_more",
                        use_container_width=True,
                    ):
                        st.session_state["health_visible_count"] = visible_count + 10
                        st.rerun()

    # Weekly plan feature removed: simplified single-view container used instead of tabs


def render_mood() -> None:
    
    st.title("Come ti senti oggi?")
    st.caption(
        "Sposta gli slider verso il polo che ti rappresenta di più. "
        "Zero significa nessuna preferenza su quella dimensione."
    )

    model = get_mood_based_model()

    col1, col2 = st.columns(2)

    with col1:
        body = st.slider(
            "Body — leggero ↔ di cuore",
            -5.0,
            5.0,
            0.0,
            step=0.5,
            help="Negativo: vuoi mangiare leggero. Positivo: vuoi mangiare di cuore.",
            key="mood_body",
        )
        taste = st.slider(
            "Taste — delicato ↔ ricco",
            -5.0,
            5.0,
            0.0,
            step=0.5,
            help="Negativo: sapore delicato. Positivo: sapore intenso e grasso.",
            key="mood_taste",
        )
        mental = st.slider(
            "Mental — salutare ↔ confortante",
            -5.0,
            5.0,
            0.0,
            step=0.5,
            help="Negativo: vuoi sentirti in forma. Positivo: vuoi coccolarti.",
            key="mood_mental",
        )

    with col2:
        time = st.slider(
            "Time — veloce ↔ elaborato",
            -5.0,
            5.0,
            0.0,
            step=0.5,
            help="Negativo: hai poco tempo. Positivo: vuoi cucinare con cura.",
            key="mood_time",
        )
        price = st.slider(
            "Price — economico ↔ costoso",
            -5.0,
            5.0,
            0.0,
            step=0.5,
            help="Negativo: vuoi spendere poco. Positivo: puoi permetterti ingredienti costosi.",
            key="mood_price",
        )
        modification = st.slider(
            "Modification — classico ↔ sperimentale",
            -5.0,
            5.0,
            0.0,
            step=0.5,
            help="Negativo: vuoi qualcosa di tradizionale. Positivo: vuoi sperimentare.",
            key="mood_modification",
        )

    top_k = st.number_input(
        "Quante ricette mostrare",
        min_value=3,
        max_value=30,
        value=10,
        step=1,
        key="mood_top_k",
    )

    st.markdown("---")

    results = model.recommend(
        body=body,
        mental=mental,
        taste=taste,
        time=time,
        price=price,
        modification=modification,
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
        return

    st.caption(f"{len(results)} ricette più vicine al tuo mood attuale")
    for i, r in enumerate(results):
        scores = r["mood_scores"]
        ingredients, steps = get_recipe_details(model, r["id"])
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


def render_collaborative() -> None:
    st.markdown(
        '<p class="eyebrow">Modello 5 — Filtro collaborativo (SVD)</p>',
        unsafe_allow_html=True,
    )
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

    top_k = st.number_input(
        "Quante ricette mostrare",
        min_value=3,
        max_value=30,
        value=10,
        step=1,
        key="collab_top_k",
    )

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
        return

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
        return

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


def render_hybrid() -> None:
    st.markdown(
        '<p class="eyebrow">Modello 5 — Combinazione context-aware</p>',
        unsafe_allow_html=True,
    )
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
        st.success(
            f"Stai usando il profilo utente **{user_id}** — se ha abbastanza "
            "interazioni, il Collaborative Filtering sarà attivo."
        )
    else:
        st.info(
            "Nessuno User ID impostato — il modello tratterà la richiesta "
            "come un nuovo utente (cold start)."
        )

    st.markdown("---")

    tab_mood, tab_fridge, tab_health = st.tabs(
        ["🎭 Mood", "🥗 Svuota-Frigo", "🥦 Vincoli salutistici"]
    )

    with tab_mood:
        use_mood = st.checkbox(
            "Attiva il mood in questa raccomandazione",
            key="hy_use_mood",
        )
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
                modification = st.slider(
                    "Modification",
                    -5.0,
                    5.0,
                    0.0,
                    step=0.5,
                    key="hy_mod",
                )
            mood_params = {
                "body": body,
                "mental": mental,
                "taste": taste,
                "time": time,
                "price": price,
                "modification": modification,
            }

    with tab_fridge:
        ingredients_raw = st.text_input(
            "Ingredienti disponibili (lascia vuoto per non attivare)",
            placeholder="es. chicken, garlic, lemon",
            key="hy_ingredients",
        )
        user_ingredients = (
            [i.strip() for i in ingredients_raw.split(",") if i.strip()]
            if ingredients_raw.strip()
            else None
        )

    with tab_health:
        use_health = st.checkbox(
            "Attiva i vincoli nutrizionali in questa raccomandazione",
            key="hy_use_health",
        )
        health_params = None
        if use_health:
            c1, c2 = st.columns(2)
            with c1:
                hy_max_cal = st.slider(
                    "Calorie massime",
                    100,
                    1500,
                    600,
                    step=50,
                    key="hy_maxcal",
                )
                hy_profile = st.selectbox(
                    "Obiettivo",
                    ["balanced", "weight_loss", "muscle_gain"],
                    key="hy_profile",
                )
            with c2:
                hy_min_prot = st.slider(
                    "Proteine minime (% DV)",
                    0,
                    100,
                    20,
                    step=5,
                    key="hy_minprot",
                )
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

    top_k = st.number_input(
        "Quante ricette mostrare",
        min_value=3,
        max_value=30,
        value=10,
        step=1,
        key="hy_top_k",
    )
    run = st.button("Genera raccomandazioni", type="primary", key="hy_run")

    if not run:
        st.markdown(
            empty_state_html("Imposta i parametri che vuoi e premi «Genera raccomandazioni»."),
            unsafe_allow_html=True,
        )
        return

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
        return

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


PAGE_RENDERERS = {
    "home": render_home,
    "popularity": render_popularity,
    "svuota_frigo": render_svuota_frigo,
    "salutistico": render_salutistico,
    "mood": render_mood,
    "collaborative": render_collaborative,
    "hybrid": render_hybrid,
}
