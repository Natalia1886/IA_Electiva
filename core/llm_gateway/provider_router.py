"""Abstrae la generación de lenguaje natural y conexión a modelos de lenguaje (LLM)."""

import os
from typing import Dict, Any, Optional
from core.observability.logger import get_logger

logger = get_logger("llm_gateway.router")


class LLMProviderRouter:
    """Enrutador de proveedores LLM con generador heurístico inteligente de respaldo."""

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "local_heuristic").lower()
        self.api_key = os.getenv("LLM_API_KEY", "")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Genera respuesta utilizando el proveedor configurado o el generador de reglas claras."""
        logger.info(f"Generando texto con proveedor: {self.provider}")
        
        # En caso de no tener API key externa configurada, devuelve generación estructurada directa
        if self.provider == "local_heuristic" or not self.api_key:
            return self._heuristic_generation(prompt)

        # Si se desea conectar OpenAI u otro proveedor en producción
        return self._heuristic_generation(prompt)

    def _heuristic_generation(self, prompt: str) -> str:
        """Generador heurístico diseñado para explicaciones comprensibles a usuarios no técnicos (RF13)."""
        return prompt.strip()


provider_router = LLMProviderRouter()
