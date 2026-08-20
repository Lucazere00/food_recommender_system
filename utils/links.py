"""Utility per costruire link verso Food.com."""
from __future__ import annotations

import re
import unicodedata
from urllib.parse import quote_plus


def _slugify(name: str) -> str:
    if not name:
        return ""
    # normalize accents
    normalized = unicodedata.normalize("NFKD", name)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    lowered = normalized.lower()
    # replace any sequence of non-alphanumeric with single dash
    slug = re.sub(r"[^0-9a-z]+", "-", lowered)
    slug = slug.strip("-")
    return slug


def build_foodcom_url(recipe: dict) -> str:
    """Costruisce un URL Food.com per `recipe`.

    Segue lo schema: https://www.food.com/recipe/<nome-slugificato>-<id>
    Se l'id non e' disponibile, ritorna un link di ricerca:
    https://www.food.com/search/<nome+with+spaces>
    """
    if not isinstance(recipe, dict):
        return "https://www.food.com/"

    # possibile colonne: 'id' o 'recipe_id'
    rid = recipe.get("id") or recipe.get("recipe_id")
    name = recipe.get("name") or ""

    slug = _slugify(str(name))
    try:
        if rid is not None:
            rid_str = str(int(rid))
            if slug:
                return f"https://www.food.com/recipe/{slug}-{rid_str}"
            return f"https://www.food.com/recipe/{rid_str}"
    except Exception:
        # fall through to search fallback
        pass

    # fallback: search URL with spaces converted to + using quote_plus
    query = quote_plus(str(name)) if name else ""
    return f"https://www.food.com/search/{query}" if query else "https://www.food.com/"
