"""Parsing LLM della richiesta libera in parametri per HybridRecommender."""

from __future__ import annotations

import json
import logging
import os
import re
import unicodedata
from typing import Any

try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None

try:
    from config import OPENAI_API_KEY
except ImportError:
    OPENAI_API_KEY = ""

logger = logging.getLogger("food_recommender.intent_parser")


EMPTY_INTENT = {
    "ingredients": None,
    "mood": None,
    "max_calories": None,
    "min_protein_pct": None,
    "tags_required": None,
    "profile_name": None,
    "exclude_ingredients": None,
}

MOOD_AXES = {"body", "time", "taste", "price", "mental", "modification"}
PROFILE_NAMES = {"balanced", "weight_loss", "muscle_gain"}
PLACEHOLDER_KEYS = {"", "sk-...", "tuo_api_key_qui", "your_api_key_here"}


def _resolve_api_key() -> str | None:
    env_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if env_key and env_key not in PLACEHOLDER_KEYS:
        return env_key

    config_key = str(OPENAI_API_KEY or "").strip()
    if config_key and config_key not in PLACEHOLDER_KEYS:
        return config_key
    return None


class LLMIntentParser:
    """Estrae ingredienti, mood e vincoli salutistici da testo naturale."""

    def __init__(self, model_name: str = "gpt-4.1-mini"):
        self.model_name = model_name
        self.api_key = _resolve_api_key()
        self.client = OpenAI(api_key=self.api_key) if self.api_key and OpenAI else None
        self.is_configured = self.client is not None
        self.last_error = None
        self.used_llm_last_call = False

    def parse_query(self, user_text: str) -> dict:
        self.used_llm_last_call = False
        if not self.client or not user_text or not user_text.strip():
            return self._fallback_parser(user_text)

        system_prompt = """
Sei il parser di intenti per un sistema Streamlit di raccomandazione ricette.
Devi convertire la richiesta libera dell'utente in un JSON valido e minimale.

Dimensioni mood ispirate a Ueda et al., valori float tra -5 e +5:
- body: +5 ricco/sostanzioso/comfort/carne, -5 leggero/fresco/insalata.
- time: +5 elaborato/lento, -5 veloce/poco tempo/stanchezza.
- taste: +5 sapori intensi/cremosi/speziati/formaggiosi, -5 delicato/semplice.
- price: +5 ingredienti costosi/ricercati, -5 economico/svuota-frigo/pochi ingredienti.
- mental: +5 gratificazione/dolce/sgarro emotivo, -5 sano/detox/nutriente.
- modification: +5 fusion/esotico/sperimentale, -5 classico/tradizionale.

Vincoli health disponibili:
- max_calories: intero, calorie massime.
- min_protein_pct: intero, proteine minime in percentuale DV.
- tags_required: tag dietetici come vegan, vegetarian, gluten-free, dairy-free, low-sodium.
- profile_name: balanced, weight_loss o muscle_gain.
- exclude_ingredients: ingredienti da escludere per allergie/avversioni.

Regole:
- Rispondi solo con JSON, senza markdown.
- Usa null per informazioni assenti.
- In "mood" includi solo le chiavi davvero deducibili.
- Ingredienti in inglese semplice quando possibile, es. pollo -> chicken, aglio -> garlic.
- Le negazioni come "non troppo", "niente di", "senza fretta", "non mi piace" devono invertire il segno del mood associato, non essere ignorate.
- Gli intensificatori come "molto", "davvero", "super", "-issimo/-issima" devono aumentare il valore mood verso ±5 invece di lasciare un valore fisso a ±3.
- exclude_ingredients serve per allergie/avversioni, es. "senza melanzane", "non mi piace il pesce", "sono allergico a X", "evito X".
- Se l'utente chiede ricette popolari, top-rated o più apprezzate, mantieni ingredienti/mood/health null se non sono esplicitati.
- Se l'utente parla di ingredienti disponibili, di frigo, dispensa o cosa ha a casa, estrai gli ingredienti e usa un mood price negativo.
- Non inventare vincoli non esplicitati o fortemente implicati.

Esempi:
- Input: "voglio qualcosa di molto veloce e confortante, con pollo e senza melanzane, sotto le 450 kcal"
  Output: {"ingredients": ["chicken"], "mood": {"body": 3.0, "time": -4.0}, "max_calories": 450, "exclude_ingredients": ["eggplant"]}
- Input: "non voglio niente di elaborato, ma sono allergico al pesce e al lattosio"
  Output: {"mood": {"time": -4.0}, "exclude_ingredients": ["fish", "dairy"]}
- Input: "super gustoso ma non troppo pesante, con pasta e senza pomodori"
  Output: {"ingredients": ["pasta"], "mood": {"taste": 4.0, "body": -3.0}, "exclude_ingredients": ["tomato"]}

Schema esatto:
{
  "ingredients": ["chicken", "garlic"] | null,
  "mood": {"body": 0.0, "time": -4.0} | null,
  "max_calories": 500 | null,
  "min_protein_pct": 20 | null,
  "tags_required": ["vegetarian"] | null,
  "profile_name": "balanced" | "weight_loss" | "muscle_gain" | null,
  "exclude_ingredients": ["eggplant"] | null
}
""".strip()

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            raw_content = response.choices[0].message.content or "{}"
            self.last_error = None
            self.used_llm_last_call = True
            logger.info("Chiamata OpenAI riuscita per input: %r -> %s", user_text, raw_content)
            return self._normalize_intent(json.loads(raw_content))
        except Exception as exc:
            self.last_error = exc.__class__.__name__
            self.used_llm_last_call = False
            logger.error(
                "Chiamata OpenAI fallita (%s): %s | input: %r",
                exc.__class__.__name__, str(exc), user_text,
                exc_info=True,
            )
            if "model" in str(exc).lower():
                logger.error(
                    "Il modello '%s' potrebbe non essere disponibile per questa API "
                    "key. Prova 'gpt-4o-mini' o verifica i modelli abilitati sul tuo "
                    "account OpenAI.",
                    self.model_name,
                )
            return self._fallback_parser(user_text)

    @staticmethod
    def _empty_intent() -> dict:
        return dict(EMPTY_INTENT)

    def _normalize_text(self, user_text: str) -> str:
        if not user_text:
            return ""
        normalized = unicodedata.normalize("NFKD", str(user_text).lower())
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        normalized = normalized.replace("’", "'").replace("–", "-").replace("—", "-")
        normalized = re.sub(r"[^a-z0-9\s\-+/]+", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _fallback_parser(self, user_text: str) -> dict:
        """Fallback locale più robusto quando l'API non risponde."""
        intent = self._empty_intent()
        text = self._normalize_text(user_text)
        if not text.strip():
            return intent

        mood = {}

        negation_tokens = {
            "non", "no", "niente", "nessun", "nessuna", "senza", "evito", "evitare",
            "avoid", "without", "dont", "don't", "nope"
        }

        def _has_negation(phrase: str, window_size: int = 3) -> bool:
            for match in re.finditer(rf"\b{re.escape(phrase)}\b", text):
                prefix_tokens = text[:match.start()].split()
                context_tokens = prefix_tokens[-window_size:]
                if any(token in negation_tokens for token in context_tokens):
                    return True
            return False

        def _stem_match(phrase: str, target_text: str) -> bool:
            if re.search(rf"\b{re.escape(phrase)}\b", target_text):
                return True
            if " " in phrase:
                return False
            stem = re.sub(r"[aoei]$", "", phrase)
            if len(stem) < 4 or stem == phrase:
                return False
            return bool(re.search(rf"\b{re.escape(stem)}[a-z]*\b", target_text))

        def _apply_phrase(axis: str, phrase: str, base_value: float) -> None:
            if axis not in MOOD_AXES:
                return
            if not _stem_match(phrase, text):
                return
            signed_value = base_value
            if _has_negation(phrase):
                signed_value *= -1
            mood[axis] = mood.get(axis, 0.0) + signed_value

        intensifier_multiplier = 1.0
        if re.search(r"\b(molto|davvero|super|troppo|assai|estremamente)\b", text):
            intensifier_multiplier = 1.4
        if re.search(r"\b([a-z]+)(issimo|issima|issimi|issime)\b", text):
            intensifier_multiplier = 1.6

        axis_phrase_sets = {
            "body": {
                "positive": [
                    "di cuore", "hearty", "sostanzioso", "pesante", "caldo", "cozy", "warm"
                ],
                "negative": [
                    "leggero", "leggera", "light", "fresco", "insalata", "salad",
                    "diet", "detox", "sano", "salutare", "nutriente", "healthy", "clean"
                ],
            },
            "mental": {
                "positive": [
                    "dolce", "desert", "dessert", "sgarro", "treat", "stress", "emotional",
                    "coccola", "confort", "confortante", "comfort", "comfortante",
                    "mi coccolo", "mi voglio coccolare", "voglio premiarmi", "mi merito"
                ],
                "negative": ["detox", "sano", "healthy", "salutare", "nutriente", "light", "diet", "clean"],
            },
            "time": {
                "positive": [
                    "elaborato", "lento", "slow", "con calma", "cucinare con cura", "per festa",
                    "weekend", "domani", "special occasion"
                ],
                "negative": [
                    "veloce", "rapido", "poco tempo", "subito", "quick", "fast", "in fretta",
                    "stanco", "stanca", "busy", "hurry", "no time", "facile", "easy", "fretta",
                    "di corsa", "corro", "non ho tempo", "poco tempo a disposizione"
                ],
            },
            "taste": {
                "positive": [
                    "gustoso", "gustosa", "gustosi", "gustose", "saporito", "saporita", "cremoso", "piccante", "spicy",
                    "savory", "gourmet", "sfizioso", "speciale", "rich", "intenso", "squisitissimo", "squisitissima", "squisitissimi", "squisitissime"
                ],
                "negative": ["delicato", "semplice", "simple", "bland", "plain", "light"],
            },
            "price": {
                "positive": ["costoso", "luxury", "ricercato", "fancy", "speciale", "gourmet"],
                "negative": [
                    "economico", "economica", "budget", "cheap", "low cost", "basso costo",
                    "pochi ingredienti", "svuota frigo", "frigo", "dispensa", "a casa",
                    "ingredienti disponibili", "ingredienti a casa", "in frigo", "in dispensa",
                    "al verde", "spendere poco", "spendere il minimo", "risparmiare",
                    "senza spendere"
                ],
            },
            "modification": {
                "positive": [
                    "sperimentale", "esotico", "fusion", "innovativo", "adventurous",
                    "ethnic", "strano", "curioso", "avventuroso",
                    "provare qualcosa di nuovo", "cambiare", "uscire dalla routine",
                    "diverso dal solito"
                ],
                "negative": ["classico", "tradizionale", "traditional", "classic", "tipico"],
            },
        }

        nutritional_terms = (
            "proteine", "proteina", "proteico", "carboidrati", "grassi", "fibre",
            "vitamine", "nutrienti"
        )
        if _stem_match("ricco", text) and not any(term in text for term in nutritional_terms):
            mood["taste"] = mood.get("taste", 0.0) + 3.0 * intensifier_multiplier

        for axis, groups in axis_phrase_sets.items():
            for phrase in groups["positive"]:
                _apply_phrase(axis, phrase, 3.0 * intensifier_multiplier)
            for phrase in groups["negative"]:
                _apply_phrase(axis, phrase, -3.0 * intensifier_multiplier)

        if any(phrase in text for phrase in ("senza fretta", "senza pressa", "con calma", "cucinare con calma", "senza urgenza", "non in fretta")):
            mood["time"] = max(mood.get("time", 0.0), 3.0 * intensifier_multiplier)

        if "economico" in text or "economica" in text or "budget" in text or "cheap" in text:
            mood["price"] = mood.get("price", 0.0) - 3.0 * intensifier_multiplier
        if "speciale" in text or "gourmet" in text or "ricercato" in text or "fancy" in text:
            mood["taste"] = mood.get("taste", 0.0) + 3.0 * intensifier_multiplier

        if any(term in text for term in ("detox", "light", "salutare", "healthy", "nutriente")):
            mood["body"] = min(mood.get("body", 0.0), -3.0)
            mood["mental"] = min(mood.get("mental", 0.0), -3.0)
            intent["profile_name"] = "balanced"

        calories_match = re.search(
            r"(?:sotto|meno di|max|massimo|entro|fino a|under|less than|<=|<)\s*(?:le|i|a)?\s*(\d{2,4})\s*(?:k?cal|calorie|cal)\b",
            text,
        )
        if not calories_match:
            calories_match = re.search(r"\b(\d{2,4})\s*(?:k?cal|calorie|cal)\b", text)
        if calories_match:
            intent["max_calories"] = self._positive_int(calories_match.group(1))

        protein_match = re.search(
            r"(?:proteine|proteina|protein)\s*(?:almeno|minimo|min|a)?\s*(\d{1,3})(?:\s*%|\s*percentuale)?",
            text,
        )
        if re.search(r"\b(proteina|proteine|protein)\b", text) and not protein_match:
            intent["min_protein_pct"] = 20
        elif protein_match:
            intent["min_protein_pct"] = self._positive_int(protein_match.group(1))

        tag_map = {
            "vegan": ["vegano", "vegan", "plant based", "plant-based"],
            "vegetarian": ["vegetariano", "vegetariana", "vegetarian"],
            "gluten-free": ["senza glutine", "gluten free", "gluten-free", "no gluten", "without gluten", "glutine", "gluten"],
            "dairy-free": ["senza lattosio", "senza latte", "dairy free", "dairy-free", "lactose free", "lactose-free", "without dairy", "lattosio", "latte"],
            "low-sodium": ["poco sodio", "low sodium", "low-sodium", "sodium-free", "low salt"],
            "high-protein": ["high protein", "high-protein", "proteico", "protein rich", "protein-rich"],
            "low-carb": ["low carb", "low-carb", "basso carboidrati", "a basso carboidrati", "carb-free"],
            "sugar-free": ["senza zucchero", "sugar free", "sugar-free", "no sugar"],
        }
        tags = [tag for tag, phrases in tag_map.items() if any(phrase in text for phrase in phrases)]
        intent["tags_required"] = sorted(set(tags)) or None

        ingredient_map = {
            "chicken": ["pollo", "chicken", "chicken breast", "petto di pollo"],
            "garlic": ["aglio", "garlic", "spicchio d aglio"],
            "rice": ["riso", "rice"],
            "pasta": ["pasta"],
            "egg": ["uovo", "uova", "egg", "eggs"],
            "tuna": ["tonno", "tuna"],
            "tomato": ["pomodoro", "pomodori", "pomodoroo", "tomato", "tomatoes"],
            "zucchini": ["zucchine", "zucchini"],
            "potatoes": ["patate", "potatoes", "potato"],
            "lentils": ["lenticchie", "lentils", "lentil"],
            "chickpeas": ["ceci", "chickpeas", "chickpea", "fagioli"],
            "salmon": ["salmone", "salmon"],
            "beef": ["manzo", "beef", "bistecca"],
            "onion": ["cipolla", "cipolle", "onion", "onions"],
            "broccoli": ["broccoli", "broccolo"],
            "tofu": ["tofu"],
            "carrot": ["carota", "carotte", "carrot", "carrots"],
            "spinach": ["spinaci", "spinach"],
            "mushrooms": ["funghi", "mushroom", "mushrooms"],
            "beans": ["fagioli", "beans", "bean"],
            "cheese": ["formaggio", "cheese"],
            "olive oil": ["olio d oliva", "olive oil", "olio"],
            "butter": ["burro", "butter"],
            "bread": ["pane", "bread"],
            "apple": ["mela", "apple", "apples"],
            "banana": ["banana", "banane"],
            "lemon": ["limone", "lemon", "lemons"],
            "yogurt": ["yogurt", "yogurt greco"],
            "cream": ["crema", "cream"],
            "coconut milk": ["latte di cocco", "coconut milk"],
            "corn": ["mais", "corn"],
            "peas": ["piselli", "peas"],
            "cucumber": ["cetriolo", "cucumber", "cucumbers"],
            "avocado": ["avocado", "avocado"],
            "pepper": ["peperone", "peperoni", "pepper", "peppers"],
            "chili": ["peperoncino", "chili", "chilli"],
            "ginger": ["zenzero", "ginger"],
            "soy sauce": ["salsa di soia", "soy sauce"],
            "sesame": ["sesamo", "sesame"],
            "eggplant": ["melanzana", "melanzane", "eggplant", "eggplants"],
            "fish": ["pesce", "fish", "salmon", "tonno", "tuna", "salmone"],
            "nuts": ["nocciola", "nocciole", "noci", "nut", "nuts"],
            "dairy": ["latte", "lattosio", "dairy", "cheese", "yogurt", "burro", "cream"],
        }
        exclusion_map = {
            "eggplant": ["melanzana", "melanzane", "eggplant", "eggplants"],
            "fish": ["pesce", "fish", "salmon", "tonno", "tuna", "salmone"],
            "nuts": ["nocciola", "nocciole", "noci", "nut", "nuts"],
            "dairy": ["latte", "lattosio", "dairy", "cheese", "yogurt", "burro", "cream"],
            "tomato": ["pomodoro", "pomodori", "pomodoroo", "tomato", "tomatoes"],
            "chicken": ["pollo", "chicken", "chicken breast", "petto di pollo"],
            "garlic": ["aglio", "garlic", "spicchio d aglio"],
        }

        def _is_exclusion_match(phrase: str) -> bool:
            patterns = [
                rf"\bsenza\s+(?:il\s+|la\s+|i\s+|le\s+|un\s+|una\s+)?{re.escape(phrase)}\b",
                rf"\bevito\s+(?:il\s+|la\s+|i\s+|le\s+|un\s+|una\s+)?{re.escape(phrase)}\b",
                rf"\bevitar(?:e|ei|e)\s+(?:il\s+|la\s+|i\s+|le\s+|un\s+|una\s+)?{re.escape(phrase)}\b",
                rf"\bnon\s+mi\s+piace\s+(?:il\s+|la\s+|i\s+|le\s+|un\s+|una\s+)?{re.escape(phrase)}\b",
                rf"\bnon\s+voglio\s+(?:il\s+|la\s+|i\s+|le\s+|un\s+|una\s+)?{re.escape(phrase)}\b",
                rf"\ballergico(?:\s+a)?\s+(?:il\s+|la\s+|i\s+|le\s+|un\s+|una\s+)?{re.escape(phrase)}\b",
                rf"\ballergica(?:\s+a)?\s+(?:il\s+|la\s+|i\s+|le\s+|un\s+|una\s+)?{re.escape(phrase)}\b",
                rf"\ballergia\s+a\s+(?:il\s+|la\s+|i\s+|le\s+|un\s+|una\s+)?{re.escape(phrase)}\b",
            ]
            return any(re.search(pattern, text) for pattern in patterns)

        excluded = []
        for canonical, phrases in exclusion_map.items():
            if any(_is_exclusion_match(phrase) for phrase in phrases):
                excluded.append(canonical)
        intent["exclude_ingredients"] = sorted(set(excluded)) or None

        excluded_canonicals = set(intent["exclude_ingredients"] or [])
        ingredients = [
            canonical
            for canonical, phrases in ingredient_map.items()
            if canonical not in excluded_canonicals
            and any(re.search(rf"\b{re.escape(phrase)}\b", text) for phrase in phrases)
        ]
        intent["ingredients"] = sorted(set(ingredients)) or None

        if not mood and any(phrase in text for phrase in ("popolari", "piu apprezzate", "più apprezzate", "top rated", "piu votate", "più votate", "migliori")):
            intent["mood"] = None
        else:
            intent["mood"] = mood or None
        return intent

    def _normalize_intent(self, value: Any) -> dict:
        if not isinstance(value, dict):
            return self._empty_intent()

        normalized = self._empty_intent()

        ingredients = value.get("ingredients")
        if isinstance(ingredients, list):
            cleaned = [str(item).strip().lower() for item in ingredients if str(item).strip()]
            normalized["ingredients"] = cleaned or None

        mood = value.get("mood")
        if isinstance(mood, dict):
            mood_clean = {}
            for axis, raw_score in mood.items():
                axis_clean = str(axis).strip().lower()
                if axis_clean not in MOOD_AXES:
                    continue
                try:
                    score = max(-5.0, min(5.0, float(raw_score)))
                except (TypeError, ValueError):
                    continue
                mood_clean[axis_clean] = score
            normalized["mood"] = mood_clean or None

        normalized["max_calories"] = self._positive_int(value.get("max_calories"))
        normalized["min_protein_pct"] = self._positive_int(value.get("min_protein_pct"))

        exclude_ingredients = value.get("exclude_ingredients")
        if isinstance(exclude_ingredients, list):
            cleaned_exclusions = [str(item).strip().lower() for item in exclude_ingredients if str(item).strip()]
            normalized["exclude_ingredients"] = cleaned_exclusions or None

        tags = value.get("tags_required")
        if tags is None:
            tags = value.get("dietary_tags")
        if isinstance(tags, list):
            cleaned_tags = [str(tag).strip().lower() for tag in tags if str(tag).strip()]
            normalized["tags_required"] = cleaned_tags or None

        profile_name = value.get("profile_name")
        if isinstance(profile_name, str) and profile_name.strip().lower() in PROFILE_NAMES:
            normalized["profile_name"] = profile_name.strip().lower()

        return normalized

    @staticmethod
    def _positive_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            parsed = int(float(value))
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None


if not logger.handlers:
    logging.basicConfig(level=logging.INFO)
