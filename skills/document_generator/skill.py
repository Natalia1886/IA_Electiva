"""Skill: generación de documentos (docx/pdf/md)."""

from core.skill_base.base_skill import BaseSkill


class DocumentGeneratorSkill(BaseSkill):
    name = "document_generator"

    def run(self, params: dict) -> dict:
        raise NotImplementedError
