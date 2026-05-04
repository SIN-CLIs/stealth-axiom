import pytest, numpy as np
from stealth_axiom.recursive_link import RecursiveLink, LatentState
from stealth_axiom.router import AxiomRouter
from stealth_axiom.provider_learning import ProviderMemory, InnerOuterLearner

@pytest.fixture
def router():
    return AxiomRouter()

@pytest.fixture
def link():
    return RecursiveLink(input_dim=128, hidden_dim=128)

@pytest.fixture
def sample_latent():
    return LatentState(vector=np.random.randn(128), current_page_type="question_radio", previous_confidence=0.9)

@pytest.fixture
def empty_memory(tmp_path):
    return ProviderMemory(str(tmp_path / "test_memory.json"))

@pytest.fixture
def learner(empty_memory):
    return InnerOuterLearner(empty_memory)
