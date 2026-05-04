"""RecursiveLink — Latent-State-Adapter für sequentielle MAS-Kollaboration.

Überträgt Agenten-Ausgaben als konditionierten Kontext an den nächsten Agenten.
Statt rohem Text: strukturierte Vektoren mit Confidence, Fokus, Pattern-Matches.
"""
from __future__ import annotations
import json, time, logging
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── Latent State ──────────────────────────────────────────────────────────

@dataclass
class LatentState:
    """Der kontinuierliche Gedankenstrom zwischen Agenten-Layern."""
    current_page_type: str = "unknown"
    provider_name: str = "unknown"
    ax_tree_hash: str = ""            # Fingerprint des AX-Trees
    detected_elements: list = field(default_factory=list)
    previous_decision: str = ""
    previous_confidence: float = 0.0
    action_history: list = field(default_factory=list)
    provider_patterns: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_conditioning_prompt(self) -> str:
        """Wandelt LatentState in einen konditionierenden Prompt für den nächsten Agenten."""
        parts = []
        if self.current_page_type != "unknown":
            parts.append(f"Seitentyp: {self.current_page_type}")
        if self.detected_elements:
            parts.append(f"Erkannte Elemente: {', '.join(self.detected_elements[:5])}")
        if self.previous_decision:
            parts.append(f"Vorherige Entscheidung: {self.previous_decision} (Confidence: {self.previous_confidence:.0%})")
        if self.errors:
            parts.append(f"Fehler: {'; '.join(self.errors[-3:])}")
        if self.provider_patterns:
            pattern = self.provider_patterns.get(self.provider_name, {})
            if pattern:
                parts.append(f"Bekanntes Pattern für {self.provider_name}: {json.dumps(pattern)}")
        if self.action_history:
            last3 = self.action_history[-3:]
            parts.append(f"Letzte Aktionen: {' → '.join(a.get('action','?') for a in last3)}")
        return " | ".join(parts) if parts else "Keine Vorkenntnisse"

    def fork(self) -> LatentState:
        """Erzeugt eine verzweigte Kopie (für Mixture/Deliberation)."""
        return LatentState(
            current_page_type=self.current_page_type,
            provider_name=self.provider_name,
            ax_tree_hash=self.ax_tree_hash,
            detected_elements=list(self.detected_elements),
            previous_decision="",
            previous_confidence=0.0,
            action_history=list(self.action_history),
            provider_patterns=dict(self.provider_patterns),
            errors=list(self.errors),
        )

    def merge(self, other: LatentState, strategy: str = "max_confidence"):
        """Merge zwei LatentStates (für Deliberation)."""
        if strategy == "max_confidence":
            if other.previous_confidence > self.previous_confidence:
                self.previous_decision = other.previous_decision
                self.previous_confidence = other.previous_confidence
        elif strategy == "union":
            self.detected_elements = list(set(self.detected_elements + other.detected_elements))
        self.errors.extend(other.errors)
        self.errors = self.errors[-10:]


# ── RecursiveLink Adapter ─────────────────────────────────────────────────

class RecursiveLink:
    """Leichter Adapter: transformiert Agenten-Output in LatentState-Update.

    Jeder Agent gibt aus:
        { "decision": "...", "confidence": 0.95, "elements": [...], "errors": [] }

    RecursiveLink extrahiert und konditioniert den nächsten Agenten.
    """

    def __init__(self):
        self.state = LatentState()
        self.agent_counter = 0
        self.link_latency_ms = 0.0

    def process(self, agent_name: str, agent_output: dict) -> str:
        """Verarbeitet Agenten-Output, aktualisiert LatentState, gibt Conditioning-Prompt zurück."""
        start = time.time()
        self.agent_counter += 1
        self.state.action_history.append({
            "agent": agent_name,
            "action": agent_output.get("decision", ""),
            "confidence": agent_output.get("confidence", 0.0),
        })
        self.state.action_history = self.state.action_history[-20:]
        decision = agent_output.get("decision", "")
        confidence = agent_output.get("confidence", 0.0)
        if confidence > self.state.previous_confidence:
            self.state.previous_decision = decision
            self.state.previous_confidence = confidence
        elements = agent_output.get("elements", [])
        if elements:
            self.state.detected_elements = list(set(self.state.detected_elements + elements))
        page_type = agent_output.get("page_type", "")
        if page_type:
            self.state.current_page_type = page_type
        errors = agent_output.get("errors", [])
        if errors:
            self.state.errors.extend(errors)
            self.state.errors = self.state.errors[-10:]
        provider = agent_output.get("provider", "")
        if provider:
            self.state.provider_name = provider
        pattern = agent_output.get("pattern", {})
        if pattern:
            self.state.provider_patterns[agent_output.get("provider", "unknown")] = pattern
        if agent_output.get("ax_tree_hash"):
            self.state.ax_tree_hash = agent_output["ax_tree_hash"]
        self.link_latency_ms = (time.time() - start) * 1000
        prompt = self.state.to_conditioning_prompt()
        logger.debug("RecursiveLink[%s]: %s → conditioning (%d chars)", agent_name, decision[:40], len(prompt))
        return prompt

    def get_state(self) -> dict:
        return {
            "link_latency_ms": round(self.link_latency_ms, 2),
            "agent_calls": self.agent_counter,
            "state": asdict(self.state),
        }


# ── MAS Kollaborations-Patterns ──────────────────────────────────────────

class CollaborationPattern(Enum):
    SEQUENTIAL = "sequential"       # A → B → C
    MIXTURE = "mixture"             # A+B+C parallel → konsolidieren
    DELIBERATION = "deliberation"   # A ↔ B ↔ C mit Merge
    DISTILLATION = "distillation"   # Lehrer A → Schüler B

class AgentSpec:
    """Spezifikation eines Agenten in der MAS-Pipeline."""
    def __init__(self, name: str, tier: str, task_type: str, model: str = ""):
        self.name = name
        self.tier = tier
        self.task_type = task_type
        self.model = model

class MASCollaboration:
    """Orchestriert mehrere Agenten nach einem Kollaborationsmuster."""

    def __init__(self, pattern: CollaborationPattern, agents: list):
        self.pattern = pattern
        self.agents = agents
        self.links = {a.name: RecursiveLink() for a in agents}
        self.shared_state = LatentState()

    def run_sequential(self, execute_fn) -> list:
        results = []
        for i, agent in enumerate(self.agents):
            conditioning = self.links[agent.name].state.to_conditioning_prompt() if i > 0 else ""
            output = execute_fn(agent, conditioning)
            self.links[agent.name].process(agent.name, output)
            self.shared_state.merge(self.links[agent.name].state, "max_confidence")
            results.append({"agent": agent.name, "output": output})
        return results

    def run_mixture(self, execute_fn) -> list:
        from concurrent.futures import ThreadPoolExecutor
        results = []
        with ThreadPoolExecutor(max_workers=len(self.agents)) as pool:
            futures = {pool.submit(execute_fn, a, ""): a for a in self.agents}
            from concurrent.futures import as_completed
            for future in as_completed(futures):
                agent = futures[future]
                output = future.result()
                self.links[agent.name].process(agent.name, output)
                results.append({"agent": agent.name, "output": output})
        # Konsolidierung: Merge aller Ergebnisse
        for link in self.links.values():
            self.shared_state.merge(link.state, "union")
        # Highest confidence wins
        best = max(results, key=lambda r: r["output"].get("confidence", 0))
        self.shared_state.previous_decision = best["output"].get("decision", "")
        self.shared_state.previous_confidence = best["output"].get("confidence", 0.0)
        return results

    def run_deliberation(self, execute_fn, rounds: int = 2) -> list:
        results = []
        for rnd in range(rounds):
            round_results = []
            for agent in self.agents:
                conditioning = self.shared_state.to_conditioning_prompt() if rnd > 0 else ""
                output = execute_fn(agent, conditioning)
                self.links[agent.name].process(agent.name, output)
                round_results.append({"agent": agent.name, "output": output, "round": rnd})
                self.shared_state.merge(self.links[agent.name].state, "max_confidence")
            results.extend(round_results)
        return results

    def get_report(self) -> dict:
        return {
            "pattern": self.pattern.value,
            "agents": [a.name for a in self.agents],
            "states": {a.name: self.links[a.name].get_state() for a in self.agents},
            "shared": asdict(self.shared_state),
        }
