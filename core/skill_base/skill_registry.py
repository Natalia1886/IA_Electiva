"""Registro central de skills disponibles para los agentes."""

SKILL_REGISTRY: dict = {}


def register_skill(skill_cls):
    SKILL_REGISTRY[skill_cls.name] = skill_cls
    return skill_cls
