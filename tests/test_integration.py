from stealth_axiom.router import AxiomRouter
from stealth_axiom.recursive_link import RecursiveLink
from stealth_axiom.survey_mas import SurveyOrchestrator
from stealth_axiom.provider_learning import ProviderMemory, InnerOuterLearner

class TestFullIntegration:
    def test_survey_flow_with_learning(self, tmp_path):
        router = AxiomRouter()
        link = RecursiveLink()
        memory = ProviderMemory(str(tmp_path / "memory.json"))
        learner = InnerOuterLearner(memory)
        context = {"ax_tree": "... AXRadioButton ... AXButton", "body": "Stimmen Sie zu?"}
        orch = SurveyOrchestrator(router, link)
        survey_result = orch.run(context)
        learner.inner_loop("samplicio", {"had_consent": True, "question_types": ["radio"],
            "success": survey_result["results"][-1]["verifier"]["success"]})
        strategy = learner.outer_loop("samplicio")
        assert strategy["expected_consent"] is True
        assert strategy["suggested_first_action"] == "click_consent"
