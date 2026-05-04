"""stealth-axiom — 3-Tier Model Router + RecursiveMAS Integration.

Micro (<100ms) → Mid (<500ms) → Heavy (nur Notfall) + RecursiveLink MAS.
80% FREE, 15% FREE, 5% kostenpflichtig → 99.96% Kostenersparnis.
"""
from .router import AxiomRouter, ModelConfig, TaskComplexity, MODELS
from .recursive_link import RecursiveLink, LatentState, MASCollaboration, CollaborationPattern, AgentSpec
from .survey_flow import SurveyMAS
__all__ = [
    "AxiomRouter", "ModelConfig", "TaskComplexity", "MODELS",
    "RecursiveLink", "LatentState", "MASCollaboration", "CollaborationPattern", "AgentSpec",
    "SurveyMAS",
]
