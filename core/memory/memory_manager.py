"""API unificada de memoria para agentes y orquestador."""

from typing import Any
from core.memory.short_term import ShortTermMemory
from core.memory.long_term import LongTermMemory


class MemoryManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MemoryManager, cls).__new__(cls)
            cls._instance.short_term = ShortTermMemory()
            cls._instance.long_term = LongTermMemory()
        return cls._instance

    def remember(self, key: str, value: Any, persistent: bool = False):
        if persistent:
            self.long_term.save_insight(key, value)
        else:
            self.short_term.set(key, value)

    def recall(self, key: str, default: Any = None, persistent: bool = False) -> Any:
        if persistent:
            return self.long_term.get_insight(key, default)
        return self.short_term.get(key, default)


memory_manager = MemoryManager()
