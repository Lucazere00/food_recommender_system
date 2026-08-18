"""Spiegazioni testuali LLM per la prima raccomandazione."""

from __future__ import annotations

import os

try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None

try:
    from config import OPENAI_API_KEY
except ImportError:
    OPENAI_API_KEY = ""

PLACEHOLDER_KEYS = {"", "sk-...", "tuo_api_key_qui", "your_api_key_here"}


def _resolve_api_key() -> str | None:
    env_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if env_key and env_key not in PLACEHOLDER_KEYS:
        return env_key

    config_key = str(OPENAI_API_KEY or "").strip()
    if config_key and config_key not in PLACEHOLDER_KEYS:
        return config_key
    return None


class LLMExplainer:
    """Genera una breve motivazione in italiano per una ricetta consigliata."""

    def __init__(self, model_name: str = "gpt-4.1-mini"):
        self.model_name = model_name
        self.api_key = _resolve_api_key()
        self.client = OpenAI(api_key=self.api_key) if self.api_key and OpenAI else None
        self.is_configured = self.client is not None

    def generate_explanation(self, original_query: str, recipe: dict) -> str:
        recipe_name = str(recipe.get("name") or "questa ricetta").title()
        calories = recipe.get("calorie", recipe.get("calories"))
        fallback = self._fallback_explanation(recipe_name, recipe)
        if not self.client:
            return fallback

        system_prompt = (
            "Sei uno chef amichevole italiano. Scrivi 2-3 frasi brevi, calde "
            "e concrete, spiegando perche la ricetta proposta risponde alla "
            "richiesta originale dell'utente. Usa solo i dettagli forniti."
        )
        user_prompt = (
            f"Richiesta originale: {original_query}\n"
            f"Ricetta: {recipe_name}\n"
            f"Calorie: {calories} kcal\n"
            f"Tempo: {recipe.get('minuti')} minuti\n"
            f"Score ibrido: {recipe.get('score_ibrido_finale')}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.6,
            )
            explanation = (response.choices[0].message.content or "").strip()
            return explanation or fallback
        except Exception:
            return fallback

    @staticmethod
    def _fallback_explanation(recipe_name: str, recipe: dict) -> str:
        minutes = recipe.get("minuti")
        calories = recipe.get("calorie", recipe.get("calories"))
        score = recipe.get("score_ibrido_finale")
        return (
            f"Ti propongo {recipe_name}: e una scelta solida per la tua richiesta, "
            f"con {minutes} minuti di preparazione e circa {calories} kcal. "
            f"Il suo score ibrido ({score}) indica un buon equilibrio tra preferenze, "
            "contesto e vincoli disponibili."
        )
