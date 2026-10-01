"""Skill: búsqueda web."""

from core.skill_base.base_skill import BaseSkill


class WebSearchSkill(BaseSkill):
    name = "web_search"

    def run(self, params: dict) -> dict:
        raise NotImplementedError
