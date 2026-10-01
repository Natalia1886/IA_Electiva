"""Skill: consultas a base de datos."""

from core.skill_base.base_skill import BaseSkill


class DbQuerySkill(BaseSkill):
    name = "db_query"

    def run(self, params: dict) -> dict:
        raise NotImplementedError
