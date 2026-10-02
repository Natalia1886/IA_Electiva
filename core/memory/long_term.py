"""Memoria persistente de largo plazo (conocimiento acumulado de ventas y festividades)."""

from typing import Dict, Any


class LongTermMemory:
    def __init__(self):
        self._knowledge_base: Dict[str, Any] = {}

    def save_insight(self, key: str, data: Any):
        self._knowledge_base[key] = data

    def get_insight(self, key: str, default: Any = None) -> Any:
        return self._knowledge_base.get(key, default)
