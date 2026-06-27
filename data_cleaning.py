import pandas as pd
import re
import html
import ast
from config import (
    PATH_RAW_RECIPES,
    PATH_RAW_INTERACTIONS,
    PATH_CLEAN_RECIPES,
    PATH_CLEAN_INTERACTIONS,
    MIN_USER_INTERACTIONS,
    MIN_RECIPE_RATINGS,
    MAX_CALORIES
)

def clean_text(text):
    

    # Se il valore è mancante (NaN), lo trasforma in una stringa vuota
    if pd.isna(text):
        return ""
    
    # 1. Converte i codici entità HTML (es. &#039; diventa l'apostrofo vero)
    decoded_text = html.unescape(text)
    
    # 2. Rimuove i tag HTML (es. <br/>) usando un'espressione regolare (RegEx)
    cleaned_text = re.sub(r'<[^>]+>', ' ', decoded_text)
    
    # 3. Rimuove spazi multipli o ritorni a capo in eccesso
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text


def parse_string_to_list(string_data):
  
  
    if pd.isna(string_data):
        return []
    try:
        return ast.literal_eval(string_data)
    except (ValueError, SyntaxError):
        return []


def clean_interactions(df):
    print("-> Pulizia delle interazioni in corso...")

    # 1. Pulizia del testo nella colonna 'review'
    df['review'] = df['review'].apply(clean_text)

    # 2. Conversione della colonna 'date' nel formato datetime
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # 3. Rimozione di sicurezza delle righe senza ID (prima di qualsiasi filtro)
    df = df.dropna(subset=['user_id', 'recipe_id'])

    # 4. Ordinamento per data (garantisce che keep='last' = interazione più recente)
    df = df.sort_values(by='date')

    # 5. Gestione dei duplicati: mantiene solo l'interazione più recente
    df = df.drop_duplicates(subset=['user_id', 'recipe_id'], keep='last')

    # 6. Rimozione dei voti non validi (0 = commento puro; > 5 = corrotto)
    df = df[df['rating'].between(1, 5)]

    # 7. Rimozione recensioni troppo corte dopo la pulizia (rumore per NLP)
    df = df[df['review'].str.len() >= 10]

    # 8. Filtra utenti cold-start (basato su soglia in config.py)
    user_counts = df['user_id'].value_counts()
    df = df[df['user_id'].isin(user_counts[user_counts >= MIN_USER_INTERACTIONS].index)]

    # 9. Filtra ricette con pochi voti (basato su soglia in config.py)
    recipe_counts = df['recipe_id'].value_counts()
    df = df[df['recipe_id'].isin(recipe_counts[recipe_counts >= MIN_RECIPE_RATINGS].index)]

    return df


def clean_recipes(df):
    print("-> Pulizia delle ricette in corso...")

    # 1. Rimozione righe senza ID e conversione in intero (prima di tutto)
    df = df.dropna(subset=['id'])
    df['id'] = df['id'].astype(int)

    # 2. Pulizia dei testi (nome e descrizione)
    df['name'] = df['name'].apply(clean_text)
    df['description'] = df['description'].apply(clean_text)

    # 3. Conversione delle finte liste in vere liste Python
    for col in ['tags', 'steps', 'ingredients']:
        df[col] = df[col].apply(parse_string_to_list)

    # 4. Gestione del tempo di preparazione
    df['minutes'] = df['minutes'].replace(0, 1)
    df = df[df['minutes'] <= 4320]  # rimuove outlier > 3 giorni

    # 5. Rimuovi ricette senza ingredienti o senza steps (inutilizzabili)
    df = df[df['ingredients'].apply(len) > 0]
    df = df[df['steps'].apply(len) > 0]

    # 6. Conversione della data di sottomissione
    df['submitted'] = pd.to_datetime(df['submitted'], errors='coerce')

    # 7. Estrazione dei 7 valori nutrizionali
    print("   -> Estrazione dei singoli valori nutrizionali...")
    df['nutrition'] = df['nutrition'].apply(parse_string_to_list)
    df['calories']         = df['nutrition'].apply(lambda x: x[0] if len(x) == 7 else None)
    df['total_fat_pct']    = df['nutrition'].apply(lambda x: x[1] if len(x) == 7 else None)
    df['sugar_pct']        = df['nutrition'].apply(lambda x: x[2] if len(x) == 7 else None)
    df['sodium_pct']       = df['nutrition'].apply(lambda x: x[3] if len(x) == 7 else None)
    df['protein_pct']      = df['nutrition'].apply(lambda x: x[4] if len(x) == 7 else None)
    df['saturated_fat_pct']= df['nutrition'].apply(lambda x: x[5] if len(x) == 7 else None)
    df['carbohydrates_pct']= df['nutrition'].apply(lambda x: x[6] if len(x) == 7 else None)
    df = df.drop(columns=['nutrition'])
    
   
    print(f"   -> Rimozione ricette sopra le {MAX_CALORIES} kcal...")
    df = df.dropna(subset=['calories'])
    df = df[df['calories'] <= MAX_CALORIES]

    return df


def main():
    
    print("Caricamento RAW_interactions...")
    df_inter = pd.read_csv(PATH_RAW_INTERACTIONS)
    
    print("Caricamento RAW_recipes...")
    df_recipes = pd.read_csv(PATH_RAW_RECIPES)
    
    # Avvia la pulizia differenziata per entrambi i dataframe
    df_inter_clean = clean_interactions(df_inter)
    df_recipes_clean = clean_recipes(df_recipes)
    
    # Allineamento reciproco: tieni solo le ricette che hanno almeno
    # una interazione e viceversa (evita record orfani inutili)
    valid_recipe_ids = set(df_inter_clean['recipe_id'])
    df_recipes_clean = df_recipes_clean[df_recipes_clean['id'].isin(valid_recipe_ids)]

    valid_recipe_ids_after = set(df_recipes_clean['id'])
    df_inter_clean = df_inter_clean[df_inter_clean['recipe_id'].isin(valid_recipe_ids_after)]
    
    # Salvataggio di entrambi i file puliti
    print("Salvataggio dei file puliti in corso...")
    df_inter_clean.to_csv(PATH_CLEAN_INTERACTIONS, index=False)
    df_recipes_clean.to_csv(PATH_CLEAN_RECIPES, index=False)
    
    print("Processo di pulizia completato con successo!")
    
    


if __name__ == "__main__":
    main()