import os
import sys
import json
from groq import Groq

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import GROQ_API_KEY

class LLMIntentParser:
    def __init__(self, model_name="llama3-70b-8192"):
        """
        Inizializza il parser degli intenti usando Groq Cloud API.
        """
        self.model_name = model_name
        self.client = Groq(api_key=GROQ_API_KEY)

    def parse_query(self, user_query):
        """
        Invia la richiesta dell'utente a Llama tramite Groq per estrarre il JSON strutturato.
        """
        system_prompt = """
        Sei l'assistente di backend di un sistema di raccomandazione di ricette chiamato 'Mood-Food'.
        Il tuo compito è convertire la richiesta in linguaggio naturale dell'utente in un oggetto JSON rigoroso.
        
        Mappa gli stati psicologici ed emotivi sulle seguenti 6 dimensioni (valori float da -5.0 a +5.0):
        - body: +5.0 cibo molto sostanzioso/carne/comfort, -5.0 cibo ultra leggero/insalate.
        - mental: +5.0 sgarro emotivo/cioccolato/dolci, -5.0 cibo salutare/detox/nutritivo.
        - taste: +5.0 sapori ricchi/cremosi/speziati/formaggiosi, -5.0 sapori delicati/semplici.
        - time: +5.0 ricette elaborate/cottura lenta, -5.0 ricette super veloci (es. 'stanco', 'poco tempo').
        - price: +5.0 ingredienti costosi/ricercati, -5.0 economico/svuota-frigo/pochi ingredienti.
        - modification: +5.0 cucina fusion/esotica/sperimentale, -5.0 piatti tradizionali/classici.

        Determina anche il 'mode' più adatto:
        - "fridge": se l'utente elenca solo ingredienti che ha a disposizione.
        - "health": se l'utente si focalizza solo su diete o calorie.
        - "mood": se si focalizza solo su stati d'animo.
        - "hybrid": se mescola elementi diversi (es. ingredienti + calorie + mood).

        Rispondi ESCLUSIVAMENTE con l'oggetto JSON avente la struttura richiesta. 
        Non aggiungere introduzioni, non usare markdown, non scrivere ```json e non aggiungere testo dopo il JSON.
        
        Struttura richiesta:
        {
          "mood": {"body": 0.0, "mental": 0.0, "taste": 0.0, "time": 0.0, "price": 0.0, "modification": 0.0},
          "ingredients": ["chicken", "garlic"],
          "max_calories": 500,
          "dietary_tags": [],
          "mode": "hybrid"
        }
        """

        try:
            # Chiamata API a Groq
            chat_completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.0 # Forza il determinismo
            )
            
            json_output = chat_completion.choices[0].message.content.strip()
            
            # Pulizia di sicurezza se il modello locale inserisce comunque i backtick di markdown
            json_output = json_output.replace("```json", "").replace("```", "").strip()
            
            return json.loads(json_output)
            
        except Exception as e:
            print(f"❌ Errore durante la chiamata a Groq (Intent Parser): {e}")
            return self._fallback_parser(user_query)

    def _fallback_parser(self, query):
        query = query.lower()
        result = {
            "mood": {"body": 0.0, "mental": 0.0, "taste": 0.0, "time": 0.0, "price": 0.0, "modification": 0.0},
            "ingredients": [], "max_calories": None, "dietary_tags": [], "mode": "hybrid"
        }
        if "chicken" in query or "pollo" in query: result["ingredients"].append("chicken breast")
        if "veloce" in query or "stanco" in query: result["mood"]["time"] = -4.0
        if "triste" in query: result["mood"]["mental"] = 4.0
        return result