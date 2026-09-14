"""Shared OpenAI-key gatekeeper for AI features.

The photo/AI vision extractor was removed; this module now only exposes
:func:`valid_api_key`, used by the purchase-recommendation phrasing to decide
whether a real LLM is available.
"""
from __future__ import annotations


def valid_api_key(key: str | None) -> bool:
    return bool(key) and not (
        key in {"sk-your-key-here", "sk-REPLACE_ME"} or key.startswith("sk-your")
    )