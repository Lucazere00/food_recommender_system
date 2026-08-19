## Configurare OPENAI_API_KEY

1. Copia il file di esempio:
   `cp .streamlit/secrets.toml.example .streamlit/secrets.toml`
2. Apri `.streamlit/secrets.toml` e sostituisci il placeholder con la tua chiave vera, ottenibile da https://platform.openai.com/api-keys
3. Non committare mai `.streamlit/secrets.toml` - e` gia` in `.gitignore`, ma verifica con:
   `git check-ignore -v .streamlit/secrets.toml`
4. Riavvia `streamlit run app.py` dopo aver salvato il file.

In alternativa, per deployment come Streamlit Community Cloud, imposta la chiave dalla sezione `Secrets` del pannello dell'app invece di caricare un file.

## Usare Groq invece di OpenAI

1. Crea un account su https://console.groq.com
2. Genera una chiave dalla sezione API Keys.
3. Inseriscila in `.streamlit/secrets.toml`:
   `GROQ_API_KEY = "gsk_..."`
4. Riavvia `streamlit run app.py` dopo aver salvato il file.

Se sono presenti sia `OPENAI_API_KEY` sia `GROQ_API_KEY`, OpenAI ha priorita di default. Se OpenAI risponde con errori di quota o rate limit, l'app ritenta automaticamente con Groq.

Il modello Groq predefinito e `openai/gpt-oss-120b`. Per test o debug puoi forzare Groq passando `provider="groq"` a `LLMIntentParser()` o `LLMExplainer()`.
