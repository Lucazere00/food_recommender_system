import numpy as np
import pandas as pd


def calculate_rmse_mae(predictions):
    """
    Calcola RMSE e MAE per le predizioni del filtro collaborativo.
    predictions: lista di oggetti Prediction di scikit-surprise
                 oppure lista di tuple (voto_reale, voto_predetto).
    """
    actuals, preds = [], []

    for p in predictions:
        if hasattr(p, 'r_ui') and hasattr(p, 'est'):
            actuals.append(p.r_ui)
            preds.append(p.est)
        else:
            actuals.append(p[0])
            preds.append(p[1])

    actuals = np.array(actuals)
    preds   = np.array(preds)

    rmse = np.sqrt(np.mean((actuals - preds) ** 2))
    mae  = np.mean(np.abs(actuals - preds))

    return {"RMSE": round(rmse, 4), "MAE": round(mae, 4)}


def calculate_ranking_metrics(recommendations_dict, test_set_df,
                               k=10, relevance_threshold=4):
    """
    Calcola Precision@K, Recall@K e NDCG@K (graded) per l'intero sistema.

    recommendations_dict: {user_id: [lista_id_ricette_raccomandate]}
    test_set_df: DataFrame con ['user_id', 'recipe_id', 'rating']
    k: top-K da valutare
    relevance_threshold: voto minimo per considerare una ricetta rilevante
    """
    precisions, recalls, ndcgs = [], [], []

    # Costruisce dizionario {user_id: {recipe_id: gain}} con rilevanza graduale
    user_relevant_items = {}
    for user_id, group in test_set_df.groupby('user_id'):
        relevant = group[group['rating'] >= relevance_threshold]
        if not relevant.empty:
            user_relevant_items[user_id] = {
                row['recipe_id']: row['rating'] - relevance_threshold + 1
                for _, row in relevant.iterrows()
            }

    for user_id, reco_items in recommendations_dict.items():
        if user_id not in user_relevant_items:
            continue

        rel_dict   = user_relevant_items[user_id]
        top_k_reco = reco_items[:k]

        # Precision@K
        n_rel_and_rec = sum(1 for item in top_k_reco if item in rel_dict)
        precisions.append(n_rel_and_rec / k)

        # Recall@K
        recalls.append(n_rel_and_rec / len(rel_dict))

        # NDCG@K graded
        dcg = 0.0
        for i, item in enumerate(top_k_reco):
            if item in rel_dict:
                dcg += rel_dict[item] / np.log2(i + 2)

        # IDCG: ranking ideale con i rilevanti in cima
        ideal_gains = sorted(rel_dict.values(), reverse=True)[:k]
        idcg = sum(g / np.log2(i + 2) for i, g in enumerate(ideal_gains))

        ndcgs.append(dcg / idcg if idcg > 0 else 0.0)

    return {
        f"Precision@{k}": round(np.mean(precisions), 4) if precisions else 0.0,
        f"Recall@{k}":    round(np.mean(recalls), 4)    if recalls    else 0.0,
        f"NDCG@{k}":      round(np.mean(ndcgs), 4)      if ndcgs      else 0.0
    }


def calculate_coverage(recommendations_dict, total_items):
    """
    Percentuale del catalogo raccomandata almeno una volta.
    Un valore basso indica che il modello tende sempre alle stesse ricette popolari.
    """
    recommended_items = set()
    for recs in recommendations_dict.values():
        recommended_items.update(recs)
    return round(len(recommended_items) / total_items, 4)


def calculate_intra_list_diversity(recommendations_dict, tfidf_matrix, recipe_id_to_idx):
    """
    Diversita media intra-lista: quanto sono diverse tra loro le ricette
    raccomandate allo stesso utente (basato su distanza coseno sui vettori TF-IDF).
    Un valore vicino a 1 indica alta diversita, vicino a 0 indica ricette molto simili.
    """
    from sklearn.metrics.pairwise import cosine_similarity

    diversities = []
    for recs in recommendations_dict.values():
        indices = [recipe_id_to_idx[r] for r in recs if r in recipe_id_to_idx]
        if len(indices) < 2:
            continue
        sub_matrix = tfidf_matrix[indices]
        sim_matrix = cosine_similarity(sub_matrix)
        # Prende solo il triangolo superiore (esclude la diagonale)
        n = sim_matrix.shape[0]
        upper = [sim_matrix[i][j] for i in range(n) for j in range(i + 1, n)]
        avg_sim = np.mean(upper)
        diversities.append(1.0 - avg_sim)

    return round(np.mean(diversities), 4) if diversities else 0.0