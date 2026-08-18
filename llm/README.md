# LLM integration

La home conversazionale usa `LLMIntentParser` e `LLMExplainer` tramite il client OpenAI.

Imposta la chiave API come variabile d'ambiente prima di avviare Streamlit:

```bash
export OPENAI_API_KEY="sk-..."
streamlit run app.py
```

Se `OPENAI_API_KEY` non e configurata, oppure contiene ancora un placeholder, la UI non va in crash: il parser restituisce parametri vuoti e la home usa il fallback cold start del recommender ibrido.
