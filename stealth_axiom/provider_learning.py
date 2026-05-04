"""Inner-Outer-Loop: pro Survey (Inner) → akkumuliert über Provider (Outer)."""
import json, logging, datetime
from pathlib import Path
logger = logging.getLogger(__name__)

class ProviderMemory:
    def __init__(self, storage_path: str = "provider_memory.json"):
        self.storage_path = Path(storage_path)
        self.memory = self._load()

    def _load(self) -> dict:
        if self.storage_path.exists():
            return json.loads(self.storage_path.read_text())
        return {"providers": {}}

    def save(self):
        self.storage_path.write_text(json.dumps(self.memory, indent=2))

    def update_provider(self, provider_name: str, new_knowledge: dict):
        prov = self.memory.setdefault("providers", {}).setdefault(provider_name, {
            "consent_pattern": None, "question_types": [], "success_rates": {}, "last_seen": None})
        prov.update(new_knowledge)
        prov["last_seen"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.save()

    def get_provider(self, provider_name: str) -> dict:
        return self.memory.get("providers", {}).get(provider_name, {})

class InnerOuterLearner:
    def __init__(self, memory: ProviderMemory):
        self.memory = memory

    def inner_loop(self, provider: str, survey_result: dict):
        consent_used = survey_result.get("had_consent", False)
        question_types = survey_result.get("question_types", [])
        success = survey_result.get("success", False)
        current = self.memory.get_provider(provider)
        known_types = set(current.get("question_types", []))
        known_types.update(question_types)
        rates = current.get("success_rates", {})
        rates["latest"] = success
        self.memory.update_provider(provider, {
            "question_types": sorted(known_types), "success_rates": rates,
            "had_consent": consent_used or current.get("had_consent", False)})

    def outer_loop(self, provider: str) -> dict:
        prov_data = self.memory.get_provider(provider)
        if not prov_data:
            return {"provider": provider, "strategy": "unbekannt", "confidence": 0.0}
        return {
            "provider": provider,
            "expected_consent": prov_data.get("had_consent", False),
            "common_question_types": prov_data.get("question_types", []),
            "suggested_first_action": "click_consent" if prov_data.get("had_consent") else "go_to_survey",
        }
