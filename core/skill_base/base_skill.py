"""Contrato que toda skill debe cumplir: input/output schema y run()."""

from abc import ABC, abstractmethod


class BaseSkill(ABC):
    name: str = "unnamed_skill"

    @abstractmethod
    def run(self, params: dict) -> dict:
        """Ejecuta la skill de forma determinística, sin estado propio."""
        raise NotImplementedError
