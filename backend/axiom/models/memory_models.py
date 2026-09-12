from pydantic import BaseModel, Field
from typing import Optional


class WorkingMemory(BaseModel):
    session_id: str = ""
    session_start: str = ""
    tokens_used_session: int = 0
    current_task: Optional[dict] = None
    active_files: list[dict] = []
    pending_subtasks: list[dict] = []
    clarification_needed: bool = False
    blocking_question: Optional[str] = None


class EpisodicMemory(BaseModel):
    user: dict = Field(default_factory=lambda: {
        "nom": "",
        "langue": "FR",
        "style_communication": "direct",
        "niveau_technique": "expert",
        "timezone": "GMT+1",
        "préfère_confirmation_avant_action": False,
    })
    patterns_observés: list[str] = []
    historique_tâches: list[dict] = []
    erreurs_apprises: list[dict] = []


class SemanticMemory(BaseModel):
    projet: dict = Field(default_factory=lambda: {
        "nom": "",
        "type": "",
        "description": "",
        "statut": "",
        "client": "",
    })
    stack_technique: dict = Field(default_factory=lambda: {
        "frontend": "",
        "backend": "",
        "base_données": "",
        "auth": "",
        "infra": "",
        "testing": "",
        "ci_cd": "",
    })
    décisions_architecturales: list[dict] = []
    contraintes_projet: list[str] = []
    glossaire: list[dict] = []


class AxiomMemory(BaseModel):
    working: WorkingMemory = Field(default_factory=WorkingMemory)
    episodic: EpisodicMemory = Field(default_factory=EpisodicMemory)
    semantic: SemanticMemory = Field(default_factory=SemanticMemory)
