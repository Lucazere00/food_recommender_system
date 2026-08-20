"""Spiegazioni testuali LLM per la prima raccomandazione."""

from __future__ import annotations

import logging

try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None

from llm._secrets import resolve_groq_key, resolve_openai_key
from llm.intent_parser import (
    DEFAULT_GROQ_MODEL,
    DEFAULT_OPENAI_MODEL,
    GROQ_FALLBACK_MODELS,
    GROQ_BASE_URL,
    SUPPORTED_PROVIDERS,
)

logger = logging.getLogger("food_recommender.explainer")


class LLMExplainer:
    """Genera una breve motivazione in italiano per una ricetta consigliata."""

    def __init__(self, model_name: str | None = None, provider: str | None = None):
        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError("provider deve essere 'openai', 'groq' oppure None")

        self._provider_forced = provider is not None
        self._requested_model_name = model_name
        self._groq_model_fallbacks_tried = set()
        self.provider = provider
        self.client = None
        self.model_name = model_name
        self.api_key = None

        self.openai_key = resolve_openai_key()
        self.groq_key = resolve_groq_key()

        chosen_provider = provider
        if chosen_provider is None:
            if self.openai_key:
                chosen_provider = "openai"
            elif self.groq_key:
                chosen_provider = "groq"

        self._activate_provider(chosen_provider, prefer_requested_model=True)

        self.is_configured = self.client is not None
        if self.provider:
            logger.info("Provider LLM attivo: %s (modello: %s)", self.provider, self.model_name)
        else:
            logger.warning(
                "Nessun provider LLM configurato (ne OPENAI_API_KEY ne GROQ_API_KEY valide). "
                "Modalita fallback attiva."
            )

    def _activate_provider(self, provider: str | None, prefer_requested_model: bool = True) -> bool:
        self.client = None
        self.api_key = None
        self.provider = None

        if OpenAI and provider == "openai" and self.openai_key:
            self.client = OpenAI(api_key=self.openai_key)
            self.api_key = self.openai_key
            self.model_name = (
                self._requested_model_name if prefer_requested_model and self._requested_model_name
                else DEFAULT_OPENAI_MODEL
            )
            self.provider = "openai"
        elif OpenAI and provider == "groq" and self.groq_key:
            self.client = OpenAI(api_key=self.groq_key, base_url=GROQ_BASE_URL)
            self.api_key = self.groq_key
            self.model_name = (
                self._requested_model_name if prefer_requested_model and self._requested_model_name
                else DEFAULT_GROQ_MODEL
            )
            self.provider = "groq"

        self.is_configured = self.client is not None
        return self.is_configured

    def _should_failover_to_groq(self, exc: Exception) -> bool:
        if self._provider_forced or self.provider != "openai" or not self.groq_key:
            return False
        error_text = f"{exc.__class__.__name__} {exc}".lower()
        return any(
            marker in error_text
            for marker in ("ratelimit", "rate_limit", "rate limit", "insufficient_quota", "quota")
        )

    def _try_next_groq_model(self, exc: Exception) -> bool:
        if self.provider != "groq":
            return False
        error_text = f"{exc.__class__.__name__} {exc}".lower()
        if not any(marker in error_text for marker in ("model_not_found", "does not exist", "not found")):
            return False

        for fallback_model in GROQ_FALLBACK_MODELS:
            if fallback_model == self.model_name or fallback_model in self._groq_model_fallbacks_tried:
                continue
            self._groq_model_fallbacks_tried.add(fallback_model)
            logger.warning(
                "Modello Groq '%s' non disponibile; ritento con '%s'.",
                self.model_name, fallback_model,
            )
            self.model_name = fallback_model
            return True
        return False
    def generate_explanation(
        self,
        original_query: str,
        recipe: dict,
        excluded_ingredients: list[str] | None = None,
        ingredient_match: bool | None = None,
    ) -> str:
        """Genera una spiegazione per `recipe`.

        Parametri aggiuntivi:
        - `excluded_ingredients`: lista di canonical ingredients che il caller ha
          verificato non essere presenti nella ricetta (passare solo se la
          verifica e' stata fatta lato codice).
        - `ingredient_match`: se fornito indica se la ricetta contiene uno
          degli ingredienti richiesti dall'utente (True/False). Se None,
          l'LLM non deve assumere nulla sulla presenza dell'ingrediente.
        """

        recipe_name = str(recipe.get("name") or "questa ricetta").title()
        calories = recipe.get("calorie", recipe.get("calories"))
        fallback = self._fallback_explanation(recipe_name, recipe)
        if not self.client:
            return fallback

        # System prompt: vieta esplicitamente qualsiasi affermazione di
        # sicurezza/assenza di allergeni a meno che non sia fornita nella
        # struttura dei dati (es. excluded_ingredients verificata dal codice
        # e ingredients della ricetta disponibili e compatibili).
        system_prompt = (
            "Sei uno chef amichevole italiano. Scrivi 2-3 frasi brevi, calde "
            "e concrete, spiegando perché la ricetta proposta risponde alla "
            "richiesta originale dell'utente. Usa solo i dettagli forniti. "
            "NON affermare mai che la ricetta sia priva di un allergene, "
            "né che sia sicura per una determinata allergia o persona, a meno "
            "che questa informazione non sia esplicitamente fornita nei campi "
            "`excluded_ingredients` (verificati dal codice) e nella lista degli "
            "`ingredients` della ricetta. Se tali informazioni non sono presenti "
            "e verificate, ometti qualsiasi riferimento a allergie, assenza di "
            "ingredienti o sicurezza alimentare."
        )

        # Prepara il contesto utente; includiamo `excluded_ingredients` solo se
        # e' stato verificato e la ricetta contiene una lista di ingredienti
        # con cui confrontare.
        user_parts = [
            f"Richiesta originale: {original_query}",
            f"Ricetta: {recipe_name}",
            f"Calorie: {calories} kcal",
            f"Tempo: {recipe.get('minuti')} minuti",
            f"Score ibrido: {recipe.get('score_ibrido_finale')}",
        ]

        verified_exclusions = None
        recipe_ings = recipe.get("ingredients")
        if excluded_ingredients and isinstance(recipe_ings, (list, tuple)) and recipe_ings:
            # normalizza e verifica che nessuna esclusione appaia nella lista
            normalized_ings = [str(i).lower() for i in recipe_ings]
            # se qualunque excluded canonical e' presente in ingredient strings,
            # consideriamo che non sia verificata l'assenza e non esponiamo
            # excluded_ingredients al modello
            if any(e in ing for e in excluded_ingredients for ing in normalized_ings):
                verified_exclusions = None
            else:
                verified_exclusions = excluded_ingredients

        if verified_exclusions:
            user_parts.append(f"Excluded ingredients verified absent: {', '.join(verified_exclusions)}")

        if ingredient_match is True:
            user_parts.append("Ingredient requested: present in this recipe (verified).")
        elif ingredient_match is False:
            user_parts.append("Ingredient requested: NOT present in this recipe (verified). Do not claim presence.")

        user_prompt = "\n".join(user_parts)

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
        except Exception as exc:
            if self._should_failover_to_groq(exc) and self._activate_provider("groq", prefer_requested_model=False):
                logger.warning(
                    "Provider OpenAI non disponibile per rate limit/quota; ritento con Groq "
                    "(modello: %s).",
                    self.model_name,
                )
                return self.generate_explanation(original_query, recipe, excluded_ingredients, ingredient_match)
            if self._try_next_groq_model(exc):
                return self.generate_explanation(original_query, recipe, excluded_ingredients, ingredient_match)
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
