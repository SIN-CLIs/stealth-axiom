#!/usr/bin/env python3
"""stealth-axiom CLI – Modell-Router-Statistiken + Routen-Test."""
import json, sys, argparse
from .router import AxiomRouter, MODELS

router = AxiomRouter()

def main():
    p = argparse.ArgumentParser(prog="stealth-axiom")
    sub = p.add_subparsers(dest="command")
    sub.add_parser("stats", help="Router-Statistiken anzeigen")
    r = sub.add_parser("route", help="Task routen und Modell ausgeben")
    r.add_argument("task_type", help="z.B. classify_element, classify_page")
    r.add_argument("--page-complexity", choices=["low", "high"], default="low")
    f = sub.add_parser("fail", help="Fehlschlag für Task-Typ verbuchen")
    f.add_argument("task_type")
    s = sub.add_parser("success", help="Erfolg für Task-Typ verbuchen")
    s.add_argument("task_type")
    sub.add_parser("health", help="Router-Health-Check")

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
        healthy = len(MODELS) == 6
        print(json.dumps({"status": "healthy" if healthy else "degraded", "models": len(MODELS),
                          "free_pct": round(sum(1 for m in MODELS.values() if m.is_free) / len(MODELS) * 100)}))

if __name__ == "__main__":
    main()
