"""Skill: ejecución de código en un entorno aislado."""

from core.skill_base.base_skill import BaseSkill


class CodeExecutorSkill(BaseSkill):
    name = "code_executor"

    def run(self, params: dict) -> dict:
        raise NotImplementedError
