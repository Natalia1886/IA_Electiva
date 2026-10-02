"""Memoria a corto plazo (volátil, contexto de la sesión actual)."""

from typing import Dict, Any


class ShortTermMemory:
    def __init__(self):
        self._store: Dict[str, Any] = {}

    def set(self, key: str, value: Any):
        self._store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def clear(self):
        self._store.clear()
