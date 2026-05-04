"""stealth-axiom — 3-Tier Model Router für die Stealth Suite.

Micro (<100ms) → Mid (<500ms) → Heavy (nur Notfall).
80% FREE, 15% FREE, 5% kostenpflichtig → 99.96% Kostenersparnis.
"""
from .router import AxiomRouter, ModelConfig, TaskComplexity, MODELS
__all__ = ["AxiomRouter", "ModelConfig", "TaskComplexity", "MODELS"]
