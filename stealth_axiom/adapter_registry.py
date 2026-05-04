"""AdapterRegistry – LoRA-Adapter Management für SIN-daemon."""
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

STEALTH_DATA = Path.home() / ".stealth"
ADAPTER_REGISTRY = STEALTH_DATA / "adapter_registry.json"
TRAIN_DATA_DIR = STEALTH_DATA / "lora_training"


class AdapterRegistry:
    """Verwaltet alle verfügbaren LoRA-Adapter. Single source of truth."""

    def __init__(self, registry_path: Path = ADAPTER_REGISTRY):
        self.registry_path = registry_path
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        if not registry_path.exists():
            self._save({"adapters": [], "active_adapter": None, "total_calls": 0})

    def _load(self) -> dict:
        return json.loads(self.registry_path.read_text())

    def _save(self, data: dict):
        self.registry_path.write_text(json.dumps(data, indent=2))

    def register(self, adapter_id: str, description: str, capability: str,
                 base_model: str = "minimax-m2p7", **meta) -> bool:
        data = self._load()
        if any(a["id"] == adapter_id for a in data["adapters"]):
            return False
        data["adapters"].append({
            "id": adapter_id,
            "description": description,
            "capability": capability,
            "base_model": base_model,
            "training_date": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": "available",
            "total_calls": 0,
            **{k: v for k, v in meta.items() if k not in ("id", "description", "capability", "base_model", "training_date", "status")},
        })
        self._save(data)
        return True

    def set_active(self, adapter_id: str) -> bool:
        data = self._load()
        if not any(a["id"] == adapter_id for a in data["adapters"]):
            return False
        data["active_adapter"] = adapter_id
        self._save(data)
        return True

    def get_active(self) -> Optional[dict]:
        data = self._load()
        active_id = data.get("active_adapter")
        if not active_id:
            return None
        for a in data["adapters"]:
            if a["id"] == active_id:
                return a
        return None

    def best_for_task(self, task_hint: str) -> Optional[dict]:
        data = self._load()
        if not data["adapters"]:
            return None
        hint = task_hint.lower()
        best, score = None, 0
        for a in data["adapters"]:
            cap = a["capability"].lower()
            desc = a["description"].lower()
            s = (3 if (cap in hint or any(w in cap for w in hint.split())) else 0)
            s += sum(1 for w in hint.split() if w in desc)
            if s > score:
                best, score = a, s
        return best

    def list_all(self) -> List[dict]:
        return self._load().get("adapters", [])

    def remove(self, adapter_id: str) -> bool:
        data = self._load()
        before = len(data["adapters"])
        data["adapters"] = [a for a in data["adapters"] if a["id"] != adapter_id]
        if data.get("active_adapter") == adapter_id:
            data["active_adapter"] = None
        self._save(data)
        return len(data["adapters"]) < before

    def record_call(self, adapter_id: str):
        data = self._load()
        for a in data["adapters"]:
            if a["id"] == adapter_id:
                a["total_calls"] = a.get("total_calls", 0) + 1
                break
        data["total_calls"] = data.get("total_calls", 0) + 1
        self._save(data)

    def get_stats(self) -> dict:
        data = self._load()
        adapters = data.get("adapters", [])
        return {
            "total_adapters": len(adapters),
            "active_adapter": data.get("active_adapter"),
            "total_calls": data.get("total_calls", 0),
            "capabilities": list(set(a["capability"] for a in adapters)),
            "adapters_by_capability": {
                cap: [a["id"] for a in adapters if a["capability"] == cap]
                for cap in set(a["capability"] for a in adapters)
            },
        }

    def model_id_for(self, adapter_id: str) -> str:
        return f"accounts/fireworks/models/{adapter_id}"

    def model_id_for_task(self, task_hint: str) -> str:
        a = self.best_for_task(task_hint)
        if a:
            return self.model_id_for(a["id"])
        return "accounts/fireworks/models/minimax-m2p7"


registry = AdapterRegistry()