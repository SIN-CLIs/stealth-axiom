#!/usr/bin/env python3
"""stealth-axiom CLI – Router + RecursiveMAS + Survey Pipeline."""
import json, sys, argparse
from .router import AxiomRouter, MODELS
from .recursive_link import RecursiveLink, MASCollaboration, CollaborationPattern, AgentSpec
from .survey_flow import SurveyMAS
from .adapter_registry import AdapterRegistry

router = AxiomRouter()

def main():
    p = argparse.ArgumentParser(prog="stealth-axiom")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("stats", help="Router-Statistiken")

    r = sub.add_parser("route", help="Task routen")
    r.add_argument("task_type")
    r.add_argument("--page-complexity", choices=["low", "high"], default="low")

    f = sub.add_parser("fail", help="Fehlschlag verbuchen")
    f.add_argument("task_type")

    s = sub.add_parser("success", help="Erfolg verbuchen")
    s.add_argument("task_type")

    sub.add_parser("health", help="Health-Check")

    # RecursiveMAS subcommands
    m = sub.add_parser("mas", help="MAS-Pipeline ausführen")
    m.add_argument("--pattern", choices=["sequential", "mixture", "deliberation"], default="sequential")
    m.add_argument("--ax-tree", default="<button>Weiter</button>")
    m.add_argument("--body", default="")

    survey = sub.add_parser("survey", help="Survey-MAS-Pipeline (4 Agenten)")
    survey.add_argument("--ax-tree", default="")
    survey.add_argument("--body", default="")
    survey.add_argument("--persona", default="Manfred, 55, männlich, Rentner aus Bayern, technik-affin")

    rl = sub.add_parser("link", help="RecursiveLink-Status")
    rl.add_argument("--show-state", action="store_true")

    ad = sub.add_parser("list-adapters", help="Alle LoRA-Adapter auflisten")
    ad.add_argument("--capability", default=None)

    sa = sub.add_parser("set-adapter", help="Aktiven Adapter setzen")
    sa.add_argument("adapter_id")

    an = sub.add_parser("analyze", help="Task mit Adapter-Routing analysieren")
    an.add_argument("task_hint")

    args = p.parse_args()
    if not args.command:
        p.print_help(); return

    if args.command == "stats":
        s = router.get_stats()
        print(json.dumps(s, indent=2))
    elif args.command == "route":
        model = router.route(args.task_type, {"page_complexity": getattr(args, "page_complexity", "low")})
        print(json.dumps({"task_type": args.task_type, "model": model.name, "provider": model.provider,
                          "tier": model.complexity.value, "is_free": model.is_free, "latency_ms": model.avg_latency_ms}, indent=2))
    elif args.command == "fail":
        router.record_failure(args.task_type)
        print(json.dumps({"recorded": "failure", "task_type": args.task_type}))
    elif args.command == "success":
        router.record_success(args.task_type)
        print(json.dumps({"recorded": "success", "task_type": args.task_type}))
    elif args.command == "health":
        healthy = len(MODELS) >= 5
        print(json.dumps({"status": "healthy" if healthy else "degraded", "models": len(MODELS),
                          "free_pct": round(sum(1 for m in MODELS.values() if m.is_free) / len(MODELS) * 100)}))
    elif args.command == "mas":
        agents = [
            AgentSpec("agent-a", "micro", "classify_element"),
            AgentSpec("agent-b", "mid", "classify_page"),
            AgentSpec("agent-c", "micro", "verify_state"),
        ]
        pattern = CollaborationPattern(args.pattern)
        collab = MASCollaboration(pattern, agents)
        results = collab.run_sequential(
            lambda a, ctx: {"decision": f"{a.name} processed", "confidence": 0.9, "elements": ["button"]}
        )
        print(json.dumps({"pattern": args.pattern, "results": results, "report": collab.get_report()}, indent=2, default=str))
    elif args.command == "survey":
        sm = SurveyMAS(persona=args.persona, router=router)
        result = sm.process(args.ax_tree, args.body)
        print(json.dumps(result, indent=2, default=str))
    elif args.command == "link":
        link = RecursiveLink()
        out1 = link.process("test-agent", {"decision": "Weiter klicken", "confidence": 0.95, "page_type": "consent"})
        state = link.get_state()
        if args.show_state:
            print(json.dumps(state, indent=2, default=str))
        else:
            print(f"Conditioning: {out1}")
            print(f"Latency: {state['link_latency_ms']}ms")
    elif args.command == "list-adapters":
        reg = AdapterRegistry()
        adapters = reg.list_all()
        if args.capability:
            adapters = [a for a in adapters if args.capability in a.get("capability", "")]
        stats = reg.get_stats()
        print(json.dumps({"stats": stats, "adapters": adapters}, indent=2, default=str))
    elif args.command == "set-adapter":
        reg = AdapterRegistry()
        ok = reg.set_active(args.adapter_id)
        active = reg.get_active()
        print(json.dumps({"ok": ok, "active": active}, indent=2, default=str))
    elif args.command == "analyze":
        reg = AdapterRegistry()
        best = reg.best_for_task(args.task_hint)
        model_id = reg.model_id_for_task(args.task_hint)
        print(json.dumps({"task_hint": args.task_hint, "best_adapter": best, "model_id": model_id}, indent=2, default=str))

if __name__ == "__main__":
    main()
