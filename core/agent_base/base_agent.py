"""Clase abstracta que define el ciclo de vida de un agente.

Todo agente concreto (en agents/) debe heredar de BaseAgent e
implementar el método run().
"""

from abc import ABC, abstractmethod


class BaseAgent(ABC):
    name: str = "unnamed_agent"

    @abstractmethod
    def run(self, task: dict) -> dict:
        """Ejecuta la tarea y devuelve un resultado estructurado."""
        raise NotImplementedError
