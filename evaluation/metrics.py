import numpy as np
import pandas as pd

def calculate_rmse_mae(predictions):
    """
    Calcola RMSE e MAE per le predizioni numeriche del filtro collaborativo.
    predictions: lista di oggetti Prediction di scikit-surprise, oppure lista di tuple (voto_reale, voto_predetto)
    """
    actuals = []
    preds = []
    
    # Gestiamo sia oggetti di Surprise sia tuple classiche
    for p in predictions:
        if hasattr(p, 'r_ui') and hasattr(p, 'est'):
            actuals.append(p.r_ui)
            preds.append(p.est)
        else:
            actuals.append(p[0])
            preds.append(p[1])
            
    actuals = np.array(actuals)
    preds = np.array(preds)
    
    rmse = np.sqrt(np.mean((actuals - preds) ** 2))
    mae = np.mean(np.abs(actuals - preds))
    
    return {"RMSE": round(rmse, 4), "MAE": round(mae, 4)}


def calculate_ranking_metrics(recommendations_dict, test_set_df, k=10, relevance_threshold=4):
    """
    Calcola Precision@K, Recall@K e NDCG@K per l'intero sistema.
    
    recommendations_dict: dizionario {user_id: [list_of_recommended_recipe_ids]}
    test_set_df: DataFrame con le interazioni di test reali, deve contenere ['user_id', 'recipe_id', 'rating']
    k: top-K elementi da valutare
    rerelevance_threshold: voto minimo per considerare una ricetta "rilevante" (es. 4 o 5)
    """
    precisions = []
    recalls = []
    ndcgs = []
    
    # Raggruppiamo gli elementi rilevanti del test set per utente per velocizzare i controlli
    user_relevant_items = {}
    for user_id, group in test_set_df.groupby('user_id'):
        # Isoliamo solo i piatti votati >= soglia
        rel_items = group[group['rating'] >= relevance_threshold]['recipe_id'].tolist()
        if rel_items:
            user_relevant_items[user_id] = set(rel_items)

    # Cicliamo su tutti gli utenti per cui abbiamo generato raccomandazioni
    for user_id, reco_items in recommendations_dict.items():
        # Se l'utente non ha elementi rilevanti nel test set, non possiamo valutarlo
        if user_id not in user_relevant_items or not user_relevant_items[user_id]:
            continue
            
        rel_set = user_relevant_items[user_id]
        # Prendiamo solo i primi K consigliati
        top_k_reco = reco_items[:k]
        
        # 1. CALCOLO PRECISION@K
        # Quanti dei primi K raccomandati sono effettivamente nel set rilevante?
        n_rel_and_rec = sum(1 for item in top_k_reco if item in rel_set)
        precision = n_rel_and_rec / k
        precisions.append(precision)
        
        # 2. CALCOLO RECALL@K
        # Quanti degli elementi rilevanti totali dell'utente sono stati intercettati nei primi K?
        recall = n_rel_and_rec / len(rel_set)
        recalls.append(recall)
        
        # 3. CALCOLO NDCG@K (Normalized Discounted Cumulative Gain)
        dcg = 0.0
        for i, item in enumerate(top_k_reco):
            if item in rel_set:
                # Formula dello sconto logaritmico basato sulla posizione (i+1)
                dcg += 1.0 / np.log2((i + 1) + 1)
                
        # Calcoliamo l'IDCG (Ideal DCG ovvero il ranking perfetto dove i rilevanti sono tutti all'inizio)
        idcg = 0.0
        ideal_hits = min(len(rel_set), k)
        for i in range(ideal_hits):
            idcg += 1.0 / np.log2((i + 1) + 1)
            
        ndcg = (dcg / idcg) if idcg > 0 else 0.0
        ndcgs.append(ndcg)
        
    # Calcoliamo la media su tutta la popolazione di utenti valutati
    return {
        f"Precision@{k}": round(np.mean(precisions), 4) if precisions else 0.0,
        f"Recall@{k}": round(np.mean(recalls), 4) if recalls else 0.0,
        f"NDCG@{k}": round(np.mean(ndcgs), 4) if ndcgs else 0.0
    }