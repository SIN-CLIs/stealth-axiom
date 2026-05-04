"""stealth-axiom — 3-Tier Router + RecursiveMAS + Provider Learning + Tests.

Micro (<100ms) → Mid (<500ms) → Heavy (Notfall). RecursiveLink-Vektoren.
Inner-Outer-Loop: pro Survey lernen, über Provider akkumulieren.
80% FREE, 15% FREE, 5% kostenpflichtig → 99.96% Kostenersparnis.
"""
from .router import AxiomRouter, ModelConfig, TaskComplexity, MODELS
from .recursive_link import RecursiveLink, LatentState, MASCollaboration, CollaborationPattern, AgentSpec
from .survey_mas import SurveyOrchestrator, SurveyAgent
from .provider_learning import ProviderMemory, InnerOuterLearner
__all__ = [
    "AxiomRouter", "ModelConfig", "TaskComplexity", "MODELS",
    "RecursiveLink", "LatentState", "MASCollaboration", "CollaborationPattern", "AgentSpec",
    "SurveyOrchestrator", "SurveyAgent",
    "ProviderMemory", "InnerOuterLearner",
]
