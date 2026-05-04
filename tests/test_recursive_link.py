import numpy as np
import pytest
from stealth_axiom.recursive_link import RecursiveLink, LatentState

class TestRecursiveLink:
    def test_project_changes_vector(self, link, sample_latent):
        proj = link.project(sample_latent)
        assert proj.vector.shape == (128,)
        assert not np.allclose(proj.vector, sample_latent.vector)

    def test_project_keeps_confidence(self, link, sample_latent):
        proj = link.project(sample_latent)
        assert proj.previous_confidence == sample_latent.previous_confidence

    def test_combine_averages_vectors(self, link):
        s1 = LatentState(vector=np.ones(128))
        s2 = LatentState(vector=np.zeros(128))
        combined = link.combine([s1, s2])
        assert np.allclose(combined.vector, 0.5)

    def test_combine_empty_returns_none(self, link):
        assert link.combine([]) is None

    def test_latent_to_dict_and_back(self, sample_latent):
        d = sample_latent.to_dict()
        restored = LatentState.from_dict(d)
        assert np.allclose(restored.vector, sample_latent.vector)
        assert restored.current_page_type == sample_latent.current_page_type

    def test_process_updates_state(self, link):
        out = link.process("test", {"decision": "Weiter", "confidence": 0.9, "page_type": "consent"})
        assert "consent" in out
        assert link.state.previous_confidence == 0.9

    def test_conditional_prompt_empty(self):
        ls = LatentState()
        assert "Keine Vorkenntnisse" in ls.to_conditioning_prompt()

    def test_fork_preserves_vector(self, sample_latent):
        f = sample_latent.fork()
        assert np.allclose(f.vector, sample_latent.vector)

    def test_merge_max_confidence(self):
        a = LatentState(previous_decision="A", previous_confidence=0.5, vector=np.ones(128))
        b = LatentState(previous_decision="B", previous_confidence=0.9, vector=np.ones(128)*2)
        a.merge(b, "max_confidence")
        assert a.previous_decision == "B"
        assert np.allclose(a.vector, b.vector)

    def test_merge_union(self):
        a = LatentState(detected_elements=["a"], vector=np.ones(128))
        b = LatentState(detected_elements=["b"], vector=np.ones(128)*3)
        a.merge(b, "union")
        assert "b" in a.detected_elements
