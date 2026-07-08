"""Viste riusabili per l'app Food Recommender."""

import streamlit as st

from data_loader import (
    get_collaborative_filtering_model,
    get_content_based_model,
    get_health_based_model,
    get_hybrid_model,
    get_mood_based_model,
    get_popularity_model,
    parse_user_id,
)
from style import empty_state_html, model_card_html, recipe_card_html


PAGE_LABELS = {
    "home": "Home",
    "popularity": "1 · Popolari",
    "svuota_frigo": "2 · Svuota-frigo",
    "salutistico": "3 · Salutistico",
    "mood": "4 · Mood",
    "collaborative": "5 · Collaborative",
    "hybrid": "6 · Ibrido",
}


def render_home() -> None:
    st.markdown(
        '<main class="home-shell">'
        '<h1 class="home-title">Cosa cuciniamo oggi?</h1>'
        '<p class="home-intro">Sei approcci diversi alla raccomandazione di '
        "ricette, costruiti sul dataset Food.com. Scegli da dove iniziare.</p>"
        "</main>",
        unsafe_allow_html=True,
    )

    st.markdown(
        model_card_html(
            icon="mood-smile",
            title="Mood-based — dimmi come ti senti",
            description="",
            icon_name="mood-smile",
            featured=True,
        ),
        unsafe_allow_html=True,
    )

    cards = [
        ("trophy", "Popolari", "Le ricette più votate, pesate con Bayesian Average."),
        ("salad", "Svuota-frigo", "Ricette dai tuoi ingredienti disponibili."),
        ("apple", "Salutistico", "Vincoli nutrizionali e piano settimanale."),
        ("users", "Collaborative", "SVD sulla cronologia degli utenti."),
        ("puzzle", "Ibrido", "Combina tutti i modelli con pesi adattivi."),
    ]

    cards_html = "".join(
        model_card_html(
            icon=icon_name,
            title=title,
            description=description,
            icon_name=icon_name,
        )
        for icon_name, title, description in cards
    )

    st.markdown(
        '<div class="model-grid">'
        f"{cards_html}"
        '<div class="model-card model-card-note">'
        "<p>Naviga dalla barra laterale. Ogni modello è indipendente e "
        "testabile da solo.</p>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_popularity() -> None:
    st.markdown(
        '<p class="eyebrow">Modello 1 — Nessun login richiesto</p>',
        unsafe_allow_html=True,
    )
    st.title("Le ricette più apprezzate")
    st.caption(
        "Punteggio calcolato con Bayesian Average: bilancia il rating medio "
        "con il numero di voti, così una ricetta con un solo 5 stelle non "
        "batte una con migliaia di recensioni solide."
    )

    model = get_popularity_model()

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        tag_input = st.text_input(
            "Filtra per tag (opzionale)",
            placeholder="es. low-carb, dessert, vegan, italian...",
            help="Inserisci esattamente un tag come compare nel dataset Food.com.",
            key="popularity_tag",
        )

    with col2:
        st.markdown("&nbsp;")
        sort_label = st.selectbox(
            "Ordina per",
            ["Score bayesiano", "Rating medio", "Numero di voti"],
            key="popularity_sort",
        )

    with col3:
        top_k = st.number_input(
            "Quante ricette",
            min_value=3,
            max_value=30,
            value=10,
            step=1,
            key="popularity_top_k",
        )

    st.markdown("---")

    tag_clean = tag_input.strip() if tag_input.strip() else None
    results = model.recommend(tag=tag_clean, top_k=int(top_k))

    sort_key_map = {
        "Score bayesiano": "score",
        "Rating medio": "rating_medio",
        "Numero di voti": "numero_voti",
    }
    results = sorted(results, key=lambda r: r[sort_key_map[sort_label]], reverse=True)

    if not results:
        st.markdown(
            empty_state_html(
                f"Nessuna ricetta trovata con il tag «{tag_clean}». "
                "Controlla l'ortografia o provane un altro."
            ),
            unsafe_allow_html=True,
        )
        return

    st.caption(
        f"{len(results)} ricette trovate"
        + (f" con il tag «{tag_clean}»" if tag_clean else "")
    )

    for r in results:
        meta = f"{r['minuti']} min · {r['calorie']} kcal · {r['numero_voti']} voti"
        st.markdown(
            recipe_card_html(
                name=r["name"].title(),
                meta=meta,
                score_label="Rating medio " + str(r["rating_medio"]),
                score_value=f"score {r['score']}",
            ),
            unsafe_allow_html=True,
        )


def render_svuota_frigo() -> None:
    st.markdown(
        '<p class="eyebrow">Modello 2 — Content-based su ingredienti</p>',
        unsafe_allow_html=True,
    )
    st.title("Cosa hai in frigo?")
    st.caption(
        "Scrivi gli ingredienti che hai disponibili, separati da virgola. "
        "Il sistema confronta il loro vettore TF-IDF con quello di ogni "
        "ricetta per trovare le corrispondenze migliori."
    )

    model = get_content_based_model()

    ingredients_raw = st.text_input(
        "Ingredienti disponibili",
        placeholder="es. chicken breast, lemon, rosemary, garlic",
        help="In inglese per maggiore precisione, dato che il dataset è in inglese.",
        key="fridge_ingredients",
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

    if not ingredients_raw.strip():
        st.markdown(
            empty_state_html(
                "Inserisci almeno un ingrediente per vedere le ricette compatibili."
            ),
            unsafe_allow_html=True,
        )
        return

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
        return

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


def render_salutistico() -> None:
    st.markdown(
        '<p class="eyebrow">Modello 3 — Constraint-based nutrizionale</p>',
        unsafe_allow_html=True,
    )
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
        diet_tags = st.multiselect(
            "Vincoli dietetici",
            ["vegan", "vegetarian", "gluten-free", "dairy-free", "low-sodium"],
            key="health_diet_tags",
        )

    tab1, tab2 = st.tabs(["Singola ricetta", "Piano settimanale"])

    with tab1:
        top_k = st.number_input(
            "Quante ricette mostrare",
            min_value=3,
            max_value=30,
            value=10,
            step=1,
            key="hb_topk",
        )

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
                meta = (
                    f"{r['minuti']} min · {r['calories']} kcal · proteine "
                    f"{r['protein_pdv']}% DV · grassi {r['fat_pdv']}% DV"
                )
                st.markdown(
                    recipe_card_html(
                        name=r["name"].title(),
                        meta=meta,
                        score_label="Health score",
                        score_value=r["health_score"],
                    ),
                    unsafe_allow_html=True,
                )

    with tab2:
        st.caption(
            "Genera un piano di 7 giorni campionando senza ripetizioni dalle "
            "ricette migliori secondo i vincoli impostati sopra."
        )

        if st.button("Genera piano settimanale", type="primary", key="weekly_plan_btn"):
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


def render_mood() -> None:
    st.markdown(
        '<p class="eyebrow">Modello 4 — Sei dimensioni emotive</p>',
        unsafe_allow_html=True,
    )
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

    if not results:
        st.markdown(
            empty_state_html("Nessuna ricetta trovata. Riprova con valori diversi."),
            unsafe_allow_html=True,
        )
        return

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
