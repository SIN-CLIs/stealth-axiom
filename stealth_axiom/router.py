"""3-Tier Model Router: Micro → Mid → Heavy, Failure-Escalation."""
import time, logging
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

MODELS = {
    "mistral-small": ModelConfig(name="mistral/mistral-small-latest", provider="mistral",
        complexity=TaskComplexity.MICRO, cost_per_call=0, avg_latency_ms=80,
        max_tokens=100, is_free=True),
    "nemotron-nano-omni": ModelConfig(name="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
        provider="nvidia", complexity=TaskComplexity.MICRO, cost_per_call=0,
        avg_latency_ms=60, max_tokens=200, is_free=True),
    "nemotron-super": ModelConfig(name="nvidia/nemotron-3-super-120b-a12b",
        provider="nvidia", complexity=TaskComplexity.MID, cost_per_call=0,
        avg_latency_ms=400, max_tokens=500, is_free=True),
    "step-flash": ModelConfig(name="nvidia/stepfun-ai/step-3.5-flash", provider="nvidia",
        complexity=TaskComplexity.MID, cost_per_call=0, avg_latency_ms=300,
        max_tokens=500, is_free=True),
    "nemoretriever-ocr": ModelConfig(name="nvidia/nemoretriever-ocr-v1", provider="nvidia",
        complexity=TaskComplexity.OCR, cost_per_call=0, avg_latency_ms=500,
        max_tokens=300, is_free=True),
    "deepseek-v4": ModelConfig(name="deepseek-v4-pro", provider="vercel",
        complexity=TaskComplexity.HEAVY, cost_per_call=0.01, avg_latency_ms=2000,
        max_tokens=4000, is_free=False),
}

class AxiomRouter:
    def __init__(self, max_free_failures=3):
        self.failure_counts = {}
        self.max_free_failures = max_free_failures
        self._stats = {"micro": 0, "mid": 0, "heavy": 0, "ocr": 0}

    def route(self, task_type: str, context: dict = None) -> ModelConfig:
        ctx = context or {}
        if task_type in ("classify_element", "pick_answer", "verify_state"):
            self._stats["micro"] += 1
            return MODELS["nemotron-nano-omni"]
        if task_type == "ocr_image":
            self._stats["ocr"] += 1
            return MODELS["nemoretriever-ocr"]
        if task_type in ("classify_page", "plan_next_action", "detect_question_type"):
            self._stats["mid"] += 1
            if ctx.get("complexity") == "high":
                return MODELS["nemotron-super"]
            return MODELS["step-flash"]
        if task_type in ("solve_math", "analyze_new_provider"):
            fails = self.failure_counts.get(task_type, 0)
            if fails >= self.max_free_failures:
                self._stats["heavy"] += 1
                logger.warning("Escalating %s to DeepSeek V4 (%d failures)", task_type, fails)
                return MODELS["deepseek-v4"]
            self._stats["mid"] += 1
            return MODELS["nemotron-super"]
        self._stats["mid"] += 1
        return MODELS["step-flash"]

    def record_failure(self, task_type: str):
        c = self.failure_counts.get(task_type, 0) + 1
        self.failure_counts[task_type] = c
        logger.info("Failure #%d for %s", c, task_type)

    def record_success(self, task_type: str):
        old = self.failure_counts.pop(task_type, None)
        if old is not None:
            logger.info("Reset failure count for %s (was %d)", task_type, old)

    def get_stats(self) -> dict:
        total = sum(self._stats.values()) or 1
        heavy_cost = self._stats["heavy"] * MODELS["deepseek-v4"].cost_per_call
        return {
            "calls": dict(self._stats), "failure_counts": dict(self.failure_counts),
            "total_calls": sum(self._stats.values()),
            "micro_pct": round(self._stats["micro"] / total * 100, 1),
            "mid_pct": round(self._stats["mid"] / total * 100, 1),
            "heavy_pct": round(self._stats["heavy"] / total * 100, 1),
            "estimated_cost_usd": round(heavy_cost, 4),
            "savings_vs_deepseek_only": round(total * 0.01 - heavy_cost, 4),
        }
