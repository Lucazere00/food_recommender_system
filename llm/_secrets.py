"""Resolver sicuro delle chiavi LLM."""

from __future__ import annotations

import os

try:
    import streamlit as st
except ModuleNotFoundError:  # pragma: no cover - dipendenza runtime opzionale nei test
    st = None


PLACEHOLDER_KEYS = {"", "sk-...", "gsk_...", "tuo_api_key_qui", "your_api_key_here"}


def _resolve_key(secret_name: str, config_fallback: str = "") -> str | None:
    key = None
    if st is not None:
        try:
            key = st.secrets.get(secret_name)
        except Exception:
            key = None
    if not key:
        key = os.environ.get(secret_name)
    if not key:
        key = config_fallback
    key = (key or "").strip()
    if not key or key in PLACEHOLDER_KEYS:
        return None
    return key


def resolve_openai_key() -> str | None:
    try:
        from config import OPENAI_API_KEY
    except ImportError:  # pragma: no cover - fallback difensivo
        OPENAI_API_KEY = ""
    return _resolve_key("OPENAI_API_KEY", OPENAI_API_KEY)


def resolve_groq_key() -> str | None:
    try:
        from config import GROQ_API_KEY
    except ImportError:  # pragma: no cover - fallback difensivo
        GROQ_API_KEY = ""
    return _resolve_key("GROQ_API_KEY", GROQ_API_KEY)


def resolve_openai_api_key() -> str | None:
    """Compatibilita con import precedenti."""
    return resolve_openai_key()
