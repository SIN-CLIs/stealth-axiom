from unittest.mock import MagicMock
from stealth_axiom.recursive_link import RecursiveLink
from stealth_axiom.survey_mas import SurveyOrchestrator

class TestSurveyMAS:
    def setup_method(self):
        self.router = MagicMock()
        self.router.route.return_value = MagicMock()
        self.link = RecursiveLink()
        self.context = {"ax_tree": "... AXRadioButton ... AXButton", "body": "Frage 1"}

    def test_orchestrator_runs_all_agents(self):
        orch = SurveyOrchestrator(self.router, self.link)
        result = orch.run(self.context)
        assert len(result["results"]) == 4

    def test_orchestrator_returns_latent(self):
        orch = SurveyOrchestrator(self.router, self.link)
        result = orch.run(self.context)
        assert result["final_latent"] is not None
        assert "vector" in result["final_latent"]
