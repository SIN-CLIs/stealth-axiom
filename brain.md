# brain.md — Architektur (stealth-axiom)

> **← [stealth-runner/brain.md](https://github.com/OpenSIN-AI/stealth-runner/blob/main/brain.md) für Gesamtarchitektur**

---

## Repo-Architektur

- **Layer**: 🧭 Router
- **Beschreibung**: 3-Tier Router + Adapter-Registry + 5-Strategien Pipeline
- **Technologie**: (Dokumentation folgt)

## Stealth Suite Integration

Dieses Repo ist Teil der Stealth Suite und MUSS:
1. NEMO Architektur respektieren (Compact Snapshot + NIM + Batch Execute — CUA-ONLY ist LEGACY/DEPRECATED)
2. Pipeline (perceive→plan→guard→execute→critique) einhalten
3. BANNED Tools vermeiden

## Abhängigkeiten

- [stealth-runner](https://github.com/OpenSIN-AI/stealth-runner) — Orchestrator
- DOC-HEALTH: `python3 /Users/jeremy/dev/stealth-runner/scripts/check_doc_health.py --repo stealth-axiom`

**Letztes Update**: 2026-05-05
