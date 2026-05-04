"""Survey-Flow als sequentielle Multi-Agent-Kollaboration (RecursiveMAS)."""
import logging, numpy as np
from .recursive_link import LatentState, RecursiveLink
from .router import AxiomRouter

logger = logging.getLogger(__name__)

class SurveyAgent:
    def __init__(self, name: str, router: AxiomRouter, link: RecursiveLink):
        self.name = name
        self.router = router
        self.link = link

    def act(self, context: dict, previous_latent: LatentState = None) -> tuple:
        raise NotImplementedError

class AXTreeParserAgent(SurveyAgent):
    def act(self, context, previous_latent=None):
        tree = context.get("ax_tree", "")
        roles = ["AXRadioButton", "AXButton", "AXTextField", "AXCheckBox"]
        vec = np.array([1 if role in tree else 0 for role in roles] + [0]*124)
        latent = LatentState(vector=vec, source_tier="micro", metadata={"roles": roles})
        return {"parsed": True}, latent

class PageClassifierAgent(SurveyAgent):
    def act(self, context, previous_latent=None):
        page_type = "question_radio" if "RadioButton" in context.get("ax_tree","") else "unknown"
        vec = previous_latent.vector * 1.1 if previous_latent else np.ones(128)
        latent = LatentState(vector=vec, source_tier="mid", metadata={"page_type": page_type})
        return {"page_type": page_type}, latent

class AnswerGeneratorAgent(SurveyAgent):
    def act(self, context, previous_latent=None):
        answer = "Ja"
        vec = previous_latent.vector + 0.5 if previous_latent else np.ones(128)
        latent = LatentState(vector=vec, source_tier="mid", metadata={"answer": answer})
        return {"answer": answer}, latent

class ActionVerifierAgent(SurveyAgent):
    def act(self, context, previous_latent=None):
        succeeded = True
        vec = previous_latent.vector - 0.2 if previous_latent else np.ones(128)
        latent = LatentState(vector=vec, source_tier="micro", metadata={"verified": succeeded})
        return {"success": succeeded}, latent

class SurveyOrchestrator:
    def __init__(self, router: AxiomRouter, link: RecursiveLink):
        self.agents = [
            AXTreeParserAgent("parser", router, link),
            PageClassifierAgent("classifier", router, link),
            AnswerGeneratorAgent("generator", router, link),
            ActionVerifierAgent("verifier", router, link),
        ]
        self.link = link

    def run(self, initial_context: dict) -> dict:
        latent = None
        results = []
        for agent in self.agents:
            res, latent = agent.act(initial_context, latent)
            results.append({agent.name: res})
        return {"results": results, "final_latent": latent.to_dict() if latent else None}
