"""Tracer para registrar trazas de ejecución de agentes y llamadas a skills."""

import time
from typing import Dict, Any, List
from core.observability.logger import get_logger

logger = get_logger("tracer")


class Tracer:
    _instance = None
    _traces: List[Dict[str, Any]] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Tracer, cls).__new__(cls)
            cls._traces = []
        return cls._instance

    def log_event(self, event_type: str, component: str, details: Dict[str, Any]):
        entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "component": component,
            "details": details
        }
        self._traces.append(entry)
        logger.info(f"[{event_type.upper()}] {component}: {details}")

    def get_traces(self) -> List[Dict[str, Any]]:
        return self._traces.copy()

    def clear(self):
        self._traces.clear()


tracer = Tracer()
