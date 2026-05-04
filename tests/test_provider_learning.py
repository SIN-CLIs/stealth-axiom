from stealth_axiom.provider_learning import ProviderMemory, InnerOuterLearner

class TestProviderLearning:
    def test_inner_loop_updates_memory(self, empty_memory, learner):
        learner.inner_loop("test_provider", {"had_consent": True, "question_types": ["radio", "text"], "success": True})
        mem = empty_memory.get_provider("test_provider")
        assert mem["had_consent"] is True
        assert "radio" in mem["question_types"]

    def test_outer_loop_suggests_consent(self, empty_memory, learner):
        learner.inner_loop("test_provider", {"had_consent": True, "question_types": [], "success": True})
        strategy = learner.outer_loop("test_provider")
        assert strategy["expected_consent"] is True
        assert strategy["suggested_first_action"] == "click_consent"

    def test_outer_loop_unknown(self, empty_memory, learner):
        strategy = learner.outer_loop("unknown")
        assert strategy["confidence"] == 0.0

    def test_memory_persistence(self, tmp_path):
        p = tmp_path / "persist.json"
        m1 = ProviderMemory(str(p))
        m1.update_provider("p1", {"had_consent": True})
        m2 = ProviderMemory(str(p))
        assert m2.get_provider("p1")["had_consent"] is True
