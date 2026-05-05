import time, logging, json, hashlib
from pathlib import Path
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)

class TaskComplexity(Enum):
    MICRO = "micro"
    MID = "mid"
    HEAVY = "heavy"
    OCR = "ocr"

class ModelConfig(dict):
    def __getattr__(self, k):
        try: return self[k]
        except KeyError: raise AttributeError(k)
    def __setattr__(self, k, v):
        self[k] = v

NVIDIA_BASE = "https://integrate.api.nvidia.com/v1"
MISTRAL_BASE = "https://api.mistral.ai/v1"

MODELS = {
    "mistral-small": ModelConfig(
        name="mistral-small-latest", provider="mistral",
        complexity=TaskComplexity.MICRO, cost_per_call=0,
        avg_latency_ms=80, max_tokens=100, is_free=True,
        base_url=MISTRAL_BASE, needs_reasoning=False),
    "nemotron-nano": ModelConfig(
        name="nvidia/nemotron-3-nano-30b-a3b", provider="nvidia",
        complexity=TaskComplexity.MID, cost_per_call=0,
        avg_latency_ms=500, max_tokens=400, is_free=True,
        base_url=NVIDIA_BASE, needs_reasoning=True),
    "nemotron-super": ModelConfig(
        name="nvidia/nemotron-3-super-120b-a12b", provider="nvidia",
        complexity=TaskComplexity.HEAVY, cost_per_call=0,
        avg_latency_ms=2000, max_tokens=800, is_free=True,
        base_url=NVIDIA_BASE, needs_reasoning=True),
    "nemotron-omni": ModelConfig(
        name="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning", provider="nvidia",
        complexity=TaskComplexity.MICRO, cost_per_call=0,
        avg_latency_ms=600, max_tokens=300, is_free=True,
        base_url=NVIDIA_BASE, needs_reasoning=True),
    "nemoretriever-ocr": ModelConfig(
        name="nvidia/nemoretriever-ocr-v1", provider="nvidia",
        complexity=TaskComplexity.OCR, cost_per_call=0,
        avg_latency_ms=500, max_tokens=300, is_free=True,
        base_url=NVIDIA_BASE, needs_reasoning=False),
}


def parse_nemotron_response(response: dict) -> str:
    for choice in response.get("choices", []):
        msg = choice.get("message", {})
        content = msg.get("content")
        if content:
            return content
        reasoning = msg.get("reasoning", "")
        if reasoning and len(reasoning) > 20:
            return reasoning.split("\n\n")[-1].strip()
    return str(response)


class AxiomRouter:
    def __init__(self, max_free_failures=3):
        self.failure_counts = {}
        self.max_free_failures = max_free_failures
        self._stats = {"micro": 0, "mid": 0, "heavy": 0, "ocr": 0}
        self._success_rates = {}
        self._llm_cache_path = Path.home() / ".stealth" / "llm_cache.json"

    def _llm_cache_get(self, prompt: str, model: str) -> Optional[dict]:
        if not self._llm_cache_path.exists():
            return None
        try:
            cache = json.loads(self._llm_cache_path.read_text())
            key = hashlib.sha256((prompt[:200] + model).encode()).hexdigest()
            return cache.get(key)
        except Exception:
            return None

    def route(self, task_type: str, context: dict = None) -> ModelConfig:
        ctx = context or {}
        if task_type in ("classify_element", "pick_answer", "verify_state"):
            self._stats["micro"] += 1
            return MODELS["mistral-small"]
        if task_type == "ocr_image":
            self._stats["ocr"] += 1
            return MODELS["nemoretriever-ocr"]
        if task_type in ("classify_page", "plan_next_action", "detect_question_type"):
            self._stats["mid"] += 1
            return MODELS["nemotron-nano"]
        if task_type in ("solve_math", "analyze_new_provider", "analyze_context"):
            fails = self.failure_counts.get(task_type, 0)
            if fails >= self.max_free_failures:
                self._stats["heavy"] += 1
                logger.warning("Escalating %s to Nemotron Super 120B (%d failures)", task_type, fails)
                return MODELS["nemotron-super"]
            self._stats["mid"] += 1
            return MODELS["nemotron-nano"]
        self._stats["mid"] += 1
        return MODELS["nemotron-nano"]

    def route_cheap_first(self, task_type: str, min_confidence: float = 0.8) -> ModelConfig:
        rate = self._success_rates.get(task_type, 1.0)
        if rate >= 0.95 and task_type in ("classify_element", "verify_state"):
            return MODELS["mistral-small"]
        return self.route(task_type)

    def record_failure(self, task_type: str):
        c = self.failure_counts.get(task_type, 0) + 1
        self.failure_counts[task_type] = c
        self._update_success_rate(task_type, 0)
        logger.info("Failure #%d for %s", c, task_type)

    def record_success(self, task_type: str):
        old = self.failure_counts.pop(task_type, None)
        if old is not None:
            logger.info("Reset failure count for %s (was %d)", task_type, old)
        self._update_success_rate(task_type, 1)

    def _update_success_rate(self, task_type: str, outcome: int):
        if task_type not in self._success_rates:
            self._success_rates[task_type] = [1.0, 0]
        sr, n = self._success_rates[task_type]
        n += 1
        self._success_rates[task_type] = [(sr * (n - 1) + outcome) / n, n]

    def get_stats(self) -> dict:
        total = sum(self._stats.values()) or 1
        return {
            "calls": dict(self._stats), "failure_counts": dict(self.failure_counts),
            "total_calls": sum(self._stats.values()),
            "micro_pct": round(self._stats["micro"] / total * 100, 1),
            "mid_pct": round(self._stats["mid"] / total * 100, 1),
            "heavy_pct": round(self._stats["heavy"] / total * 100, 1),
            "estimated_cost_usd": 0.0,
            "savings_vs_all_heavy": "100% (all free)",
            "providers": {"mistral": MISTRAL_BASE, "nvidia": NVIDIA_BASE},
        }

axiom_router = AxiomRouter()
