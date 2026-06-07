import pandas as pd
import os
import re
import html
import ast


# Definiamo i percorsi (relativi alla cartella principale)
PATH_RAW_RECIPES = "dataset/RAW_recipes.csv"
PATH_RAW_INTERACTIONS = "dataset/RAW_interactions.csv"


# Percorsi dove salvare i file una volta puliti
PATH_CLEAN_RECIPES = "dataset/clean_recipes.csv"
PATH_CLEAN_INTERACTIONS = "dataset/clean_interactions.csv"


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
    
    # 1. Pulizia del testo nella colonna 'review' tramite la funzione di supporto
    df['review'] = df['review'].apply(clean_text)
    
    # 2. Conversione della colonna 'date' nel formato datetime corretto di Pandas
    # L'argomento errors='coerce' trasforma i testi corrotti in valori nulli anziché bloccare lo script
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # 3. Gestione dei duplicati (se lo stesso utente ha commentato lo stesso piatto più volte)
    # Mantiene solo l'interazione più recente inserita nel sistema
    df = df.drop_duplicates(subset=['user_id', 'recipe_id'], keep='last')
    
    # 4. Rimozione dei voti pari a 0
    # Esclude lo 0 poiché indica commenti puri o note di testo, evitando di alterare le medie matematiche
    df = df[df['rating'] > 0]
    
    # 5. Rimozione di sicurezza delle righe in cui mancano gli identificativi chiave (ID)
    df = df.dropna(subset=['user_id', 'recipe_id'])
    
    return df


def clean_recipes(df):
   
   
    print("-> Pulizia delle ricette in corso...")
    
    # 1. Pulizia dei testi (Nomi e Descrizioni) usando la tua funzione clean_text
    df['name'] = df['name'].apply(clean_text)
    df['description'] = df['description'].apply(clean_text)
    
    # 2. Conversione delle finte liste in vere liste Python
    list_columns = ['tags', 'steps', 'ingredients']
    for col in list_columns:
        df[col] = df[col].apply(parse_string_to_list)
        
    # 3. Gestione del tempo di preparazione (0 minuti viene normalizzato a 1 minuto)
    df['minutes'] = df['minutes'].replace(0, 1)
    
    # 4. Conversione della data di sottomissione
    df['submitted'] = pd.to_datetime(df['submitted'], errors='coerce')
    
    # 5. Estrazione e separazione dei 7 valori nutrizionali fisso-sequenziali
    print("   -> Estrazione dei singoli valori nutrizionali...")
    df['nutrition'] = df['nutrition'].apply(parse_string_to_list)
    
    df['calories'] = df['nutrition'].apply(lambda x: x[0] if len(x) == 7 else None)
    df['total_fat_pct'] = df['nutrition'].apply(lambda x: x[1] if len(x) == 7 else None)
    df['sugar_pct'] = df['nutrition'].apply(lambda x: x[2] if len(x) == 7 else None)
    df['sodium_pct'] = df['nutrition'].apply(lambda x: x[3] if len(x) == 7 else None)
    df['protein_pct'] = df['nutrition'].apply(lambda x: x[4] if len(x) == 7 else None)
    df['saturated_fat_pct'] = df['nutrition'].apply(lambda x: x[5] if len(x) == 7 else None)
    df['carbohydrates_pct'] = df['nutrition'].apply(lambda x: x[6] if len(x) == 7 else None)
    
    # Rimuoviamo la vecchia colonna nutrition non più necessaria in quel formato
    df = df.drop(columns=['nutrition'])
    
    # 6. Rimozione righe senza ID e conversione finale in intero
    df = df.dropna(subset=['id'])
    df['id'] = df['id'].astype(int)
    
    return df


def main():
    
    print("Caricamento RAW_interactions...")
    df_inter = pd.read_csv(PATH_RAW_INTERACTIONS)
    
    print("Caricamento RAW_recipes...")
    df_recipes = pd.read_csv(PATH_RAW_RECIPES)
    
    # Avvia la pulizia differenziata per entrambi i dataframe
    df_inter_clean = clean_interactions(df_inter)
    df_recipes_clean = clean_recipes(df_recipes)
    
    # Salvataggio di entrambi i file puliti
    print("Salvataggio dei file puliti in corso...")
    df_inter_clean.to_csv(PATH_CLEAN_INTERACTIONS, index=False)
    df_recipes_clean.to_csv(PATH_CLEAN_RECIPES, index=False)
    
    print("Processo di pulizia completato con successo!")


if __name__ == "__main__":
    main()