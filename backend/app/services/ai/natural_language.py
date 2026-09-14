"""Natural-language phrasing layer for purchase recommendations.

The segmentation model is the *decider*: it produces the numbers (recommended
quantity, estimated demand, current stock, holiday). This module only converts
those numbers into readable Spanish, following a fixed template shape:

    Comprar N unidades de <producto>.
    Festividad próxima: <holiday>.
    Stock actual: X.
    Demanda estimada: Y.
    Razón: <motivo derivado de los datos>.

A language model may rephrase the text, but it is explicitly instructed to
*never change the numbers* — and when no LLM key is configured, the same facts
are phrased with a deterministic template. Both paths produce text backed by
the model's decision, never invented numbers.
"""
from __future__ import annotations

import json
import logging

from app.config import settings
from app.services.ai import vision

logger = logging.getLogger("milan.nlg")

SYSTEM_PROMPT = """Eres el redactor de un sistema de compras de una tienda de artículos religiosos.
Recibes un arreglo JSON con recomendaciones NUMÉRICAS ya decididas por un modelo de demanda
(por producto: code, name, current_stock, estimated_demand, suggested_quantity, upcoming_holiday y reason).

Tu única tarea es volver a redactar cada una en un texto breve y natural en español, con este formato:
"Comprar {suggested_quantity} unidades de {name}. Festividad próxima: {upcoming_holiday}. Stock actual: {current_stock}. Demanda estimada: {estimated_demand}. Razón: {reason}"
(Si un producto no tiene festividad, omite esa frase. Si no hay festividad y el motivo es el stock mínimo, adapta la razón.)

REGLAS OBLIGATORIAS:
- Usa EXACTAMENTE los números recibidos: no cambies suggested_quantity, current_stock ni estimated_demand.
- No inventes datos ni cifras que no estén en el JSON.
- No decidas ni recomiendes cantidades: eso ya está decidido.
- Devuelve ÚNICAMENTE JSON: {"recommendations": [{"code": "...", "text": "..."}, ...]}
"""
TEMPLATE_FIELDS = ("code", "name", "current_stock", "estimated_demand", "suggested_quantity", "upcoming_holiday", "reason")


def _facts(item: dict) -> dict:
    return {k: item.get(k) for k in TEMPLATE_FIELDS if item.get(k) is not None}


def _template(item: dict) -> str:
    name = item["name"]
    qty = int(item["suggested_quantity"])
    stock = int(item["current_stock"])
    demand = round(float(item.get("estimated_demand") or 0))
    reason = item.get("reason") or "proyección de demanda"

    head = f"Comprar {qty} unidades de {name}."
    if item.get("upcoming_holiday"):
        head += f" Festividad próxima: {item['upcoming_holiday']}."
    return f"{head} Stock actual: {stock}. Demanda estimada: {demand}. Razón: {reason}."


async def phrase_recommendations(items: list[dict]) -> dict[str, str]:
    """Return {code: phrased text} for every item (LLM when configured, else template)."""
    fallback = {item["code"]: _template(item) for item in items}
    if not vision.valid_api_key(settings.openai_api_key):
        return fallback

    try:
        from openai import AsyncOpenAI
    except ImportError:  # pragma: no cover
        return fallback

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        payload = [_facts(item) for item in items]
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content or "{}")
        mapping = {
            str(rec.get("code")): str(rec.get("text") or "")
            for rec in data.get("recommendations", [])
            if isinstance(rec, dict)
        }
        return {item["code"]: mapping.get(item["code"]) or fallback[item["code"]] for item in items}
    except Exception as exc:
        logger.warning("El redactor LLM falló (%s); se usa la plantilla basada en datos.", exc)
        return fallback