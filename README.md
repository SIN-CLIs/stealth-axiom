# stealth-axiom 🧠

> **3-Tier Model Router** — Micro/Mid/Heavy Hierarchischer Routing-Layer für die Stealth Suite.  
> 99.96% Kostenersparnis via Multi-Modell-Strategie.

```
┌─────────────────────────────────────────────────────────┐
│  TIER 1: MICRO (lokal-artig, <100ms)                     │
│  ┌─────────────────────────────────────────────────┐    │
│  │ nemotron-3-nano-omni-30b-a3b-reasoning (Turbo)  │    │
│  │ mistral-small-latest                             │    │
│  │ Aufgaben: Element-Klassifikation, Ja/Nein        │    │
│  │ 80% aller Calls → FREE                          │    │
│  └─────────────────────────────────────────────────┘    │
│                         ↑ fallback                       │
│  TIER 2: MID (Planung, <500ms)                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ nemotron-3-super-120b-a12b                       │    │
│  │ step-3.5-flash                                   │    │
│  │ Aufgaben: Seiten-Klassifikation, Antwort-Planung  │    │
│  │ 15% aller Calls → FREE                           │    │
│  └─────────────────────────────────────────────────┘    │
│                         ↑ fallback                       │
│  TIER 3: HEAVY (Strategie, NUR bei Notfall)              │
│  ┌─────────────────────────────────────────────────┐    │
│  │ deepseek-v4-pro (Vercel, KOSTENPFLICHTIG)        │    │
│  │ NUR: 3 Fehlschläge in Folge → 5% aller Calls    │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
pip install -e .

# Router-Statistiken
stealth-axiom stats

# Task routen
stealth-axiom route classify_element
stealth-axiom route classify_page --page-complexity high
stealth-axiom route solve_math  # 3 Fehlschläge → DeepSeek V4

# Fehlschlag/Erfolg verbuchen
stealth-axiom fail solve_math
stealth-axiom success solve_math

# Health-Check
stealth-axiom health
```

## API

```python
from stealth_axiom import AxiomRouter

router = AxiomRouter(max_free_failures_before_paid=3)

model = router.route("classify_element")
# → ModelConfig(name="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning", ...)

model = router.route("solve_math")
# → Nach 3 Failures: ModelConfig(name="deepseek-v4-pro", cost_per_call=0.01)

router.record_failure("solve_math")
router.record_success("solve_math")  # Reset counter

print(router.get_stats())
# → {"micro_pct": 80.0, "mid_pct": 15.0, "heavy_pct": 5.0, ...}
```

## Integration in stealth-session

```python
from stealth_axiom import AxiomRouter

# Im WarmExecutor
axiom = AxiomRouter()

def decide(model_input: dict) -> str:
    tier = axiom.route(model_input["task_type"], model_input.get("context", {}))
    # tier.name, tier.provider, tier.is_free, tier.avg_latency_ms
    if tier.is_free:
        return call_free_api(tier.name, model_input["prompt"])
    else:
        return call_paid_api(tier.name, model_input["prompt"])
```

## Lizenz

MIT — Teil der [SIN-CLIs Stealth Suite](https://github.com/SIN-CLIs).
