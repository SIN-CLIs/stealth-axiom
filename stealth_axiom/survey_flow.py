from __future__ import annotations
import json, time, logging
from pathlib import Path
from .recursive_link import MASCollaboration, CollaborationPattern, AgentSpec, LatentState
from .router import AxiomRouter, MODELS

logger = logging.getLogger(__name__)


def _model_for(tier: str) -> str:
    for name, cfg in MODELS.items():
        if cfg.complexity.value == tier:
            return cfg.name
    return "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"


class SurveyMAS:

    def __init__(self, persona: str = "default", router: AxiomRouter = None):
        self.persona = persona
        self.router = router or AxiomRouter()
        self.agents = [
            AgentSpec("ax-parser", "micro", "classify_element", _model_for("micro")),
            AgentSpec("page-classifier", "mid", "classify_page", _model_for("mid")),
            AgentSpec("answer-generator", "mid", "pick_answer", _model_for("mid")),
            AgentSpec("action-verifier", "micro", "verify_state", _model_for("micro")),
        ]
        self.pipeline = MASCollaboration(CollaborationPattern.SEQUENTIAL, self.agents)
        self.total_time_ms = 0.0

    def process(self, ax_tree: str, body_text: str = "", previous_context: str = "") -> dict:
        """Führt die komplette 4-Agenten-Pipeline für einen Schritt aus."""
        start = time.time()
        results = self.pipeline.run_sequential(
            lambda agent, conditioning: self._execute_agent(agent, ax_tree, body_text, conditioning)
        )
        elapsed = (time.time() - start) * 1000
        self.total_time_ms += elapsed

        return {
            "success": True,
            "pipeline_ms": round(elapsed, 2),
            "total_ms": round(self.total_time_ms, 2),
            "decision": self.pipeline.shared_state.previous_decision,
            "confidence": self.pipeline.shared_state.previous_confidence,
            "page_type": self.pipeline.shared_state.current_page_type,
            "agent_results": results,
            "links": self.pipeline.get_report(),
        }

    def _execute_agent(self, agent: AgentSpec, ax_tree: str, body_text: str, conditioning: str) -> dict:
        route = self.router.route(agent.task_type)
        prompt = self._build_prompt(agent.task_type, ax_tree, body_text, conditioning)
        return self._call_llm(route.name, prompt, agent)

    def _build_prompt(self, task: str, ax_tree: str, body_text: str, conditioning: str) -> str:
        from .prompts import get_prompt
        base = {
            "classify_element": {"line": ax_tree[:500]},
            "classify_page": {"ax_tree_snippet": ax_tree[:800]},
            "pick_answer": {"persona": self.persona, "question_text": body_text[:300], "options": ""},
            "verify_state": {"before_state": "", "after_state": ""},
        }.get(task, {})
        prompt = get_prompt(task, {"micro": "micro", "mid": "mid"}.get(task, "mid"), **base)
        if conditioning:
            prompt = f"[KONTEXT: {conditioning}]\n\n{prompt}"
        return prompt

    def _call_llm(self, model: str, prompt: str, agent: AgentSpec) -> dict:
        import os, urllib.request, hashlib

        compressed_prompt = prompt
        try:
            import sys
            sys.path.insert(0, "/Users/jeremy/dev/stealth-compressor")
            from stealth_compressor import compress as _compress
            compressed_prompt = _compress(prompt)
        except Exception:
            pass

        try:
            sys.path.insert(0, "/Users/jeremy/dev/stealth-cache")
            from stealth_cache.cache import get_cache as _get_semantic_cache
            semantic_cache = _get_semantic_cache()
            cache_hit = semantic_cache.query(compressed_prompt)
            if cache_hit:
                logger.debug("Semantic cache HIT for %s (sim=%.2f)", agent.name, cache_hit.get("similarity", 0))
                return self._parse_agent_output(agent.task_type, cache_hit["response"])
        except Exception:
            pass

        cache_key = hashlib.sha256((compressed_prompt[:200] + model).encode()).hexdigest()
        cache_path = Path.home() / ".stealth" / "llm_cache.json"
        if cache_path.exists():
            try:
                cache = json.loads(cache_path.read_text())
                if cache_key in cache:
                    logger.debug("LLM cache HIT for %s", agent.name)
                    return cache[cache_key]
            except Exception:
                pass

        api_key = os.environ.get("NVIDIA_API_KEY", "")
        if not api_key:
            env_paths = ["/Users/jeremy/dev/stealth-runner/.env", "/Users/jeremy/dev/stealth-axiom/.env"]
            for ep in env_paths:
                if os.path.exists(ep):
                    with open(ep) as f:
                        for line in f:
                            if line.startswith("NVIDIA_API_KEY="):
                                api_key = line.strip().split("=", 1)[1].strip("'\"")
                                break
        if not api_key:
            logger.warning("NVIDIA_API_KEY not found, using fallback parser")
            return self._parse_agent_output(agent.task_type, prompt[:100])

        max_tokens = self.router.route(agent.task_type).get("max_tokens", 100)

        try:
            payload = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": compressed_prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.1,
            }).encode()
            req = urllib.request.Request(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                data=payload,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {api_key}"},
            )
            resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
            content = resp["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning("LLM call failed for %s: %s", agent.name, e)
            return {"decision": "", "confidence": 0.0, "errors": [str(e)]}

        try:
            sys.path.insert(0, "/Users/jeremy/dev/stealth-optimizer")
            from stealth_optimizer import limit as _limit
            complexity = "micro" if agent.complexity.value == "micro" else "mid"
            content = _limit(content, complexity)
        except Exception:
            pass

        result = self._parse_agent_output(agent.task_type, content)

        try:
            cache = {}
            if cache_path.exists():
                try: cache = json.loads(cache_path.read_text())
                except: pass
            cache[cache_key] = result
            cache_path.write_text(json.dumps(cache))
        except Exception:
            pass

        try:
            semantic_cache.store(compressed_prompt, content, model, 0.75, agent.task_type)
        except Exception:
            pass

        return result

    def _parse_agent_output(self, task: str, content: str) -> dict:
        result = {"decision": content, "confidence": 0.8, "elements": [], "errors": []}
        if task == "classify_element":
            known = ["AXRadioButton", "AXButton", "AXTextField", "AXCheckBox", "AXStaticText", "AXGroup"]
            for k in known:
                if k in content:
                    result["elements"] = [k]
                    break
        if task == "classify_page":
            mapping = {"consent": "consent", "login": "login", "question_radio": "question_radio",
                       "finished": "finished", "unknown": "unknown"}
            for key, val in mapping.items():
                if key in content.lower():
                    result["page_type"] = val
                    break
        return result

    def get_stats(self) -> dict:
        return {
            "pipeline_ms": self.total_time_ms,
            "agents": [a.name for a in self.agents],
            "persona": self.persona,
            "state": self.pipeline.get_report(),
        }
