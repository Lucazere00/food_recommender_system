import os
import sys
from groq import Groq

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import GROQ_API_KEY

class LLMExplainer:
    def __init__(self, model_name="llama3-70b-8192"):
        """
        Inizializza l'Explainer basato su Groq Cloud API.
        """
        self.model_name = model_name
        self.client = Groq(api_key=GROQ_API_KEY)

    def generate_explanation(self, original_query, recipe_name, recipe_details):
        """
        Genera una spiegazione personalizzata in italiano usando Llama tramite Groq.
        """
        system_prompt = """
        Sei un empatico chef e nutrizionista italiano. L'utente ti ha fatto una richiesta basata sul suo stato d'animo o ingredienti.
        Il sistema ha selezionato una ricetta specifica per lui.
        Il tuo compito è scrivere una spiegazione personalizzata, brevissima (massimo 2 frasi, stile colloquiale e caloroso), 
        che colleghi la richiesta originaria dell'utente con i punti di forza della ricetta proposta.
        
        Parla in italiano, rivolgiti direttamente all'utente ("Ti consiglio...", "Questo piatto è perfetto per te perché...") 
        ed evidenzia i benefici (tempo, calorie o ingredienti). Non essere ripetitivo.
        """

        user_content = f"""
        Richiesta Utente: "{original_query}"
        Ricetta Consigliata: "{recipe_name}"
        Dettagli Ricetta: Calorie: {recipe_details.get('calorie')} kcal, Tempo: {recipe_details.get('minuti')} minuti.
        """

        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.7 # Un po' di fluidità espressiva
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ Errore durante la generazione della spiegazione con Groq: {e}")
            return f"Ho selezionato '{recipe_name}' perché rispetta i tuoi vincoli di tempo ({recipe_details.get('minuti')} min) e calorie."