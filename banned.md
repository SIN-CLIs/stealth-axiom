# banned.md — Verbotene Methoden (stealth-axiom)

> **← [stealth-runner/banned.md](https://github.com/OpenSIN-AI/stealth-runner/blob/main/banned.md) für vollständige Liste**

---

## ABSOLUT BANNED

| Tool/Methode | Grund | Ersatz |
|-------------|-------|--------|
| `webauto-nodriver` | MCP-Server, CDP-Missbrauch | cua-driver (LEGACY — NEMO is PRIMARY for surveys) |
| `skylight-cli` | DEPRECATED | `skylight-cli` RE-ACTIVATED (snapshot-compact + batch) |
| CDP Navigation/Klicks | Chrome blockiert, unsicher | cua-driver (LEGACY — NEMO is PRIMARY for surveys) |
| `pyautogui` | Mausbewegung | cua-driver (LEGACY) AXPress |
| `pynput` | Mausbewegung | cua-driver (LEGACY) AXPress |
| `pkill -f "heypiggy-bot"` | Killt USER Chrome mit! | `SessionManager.close_all()` |

## BEDINGT ERLAUBT

| Tool | Bedingung |
|------|-----------|
| CDP JS evaluate | NUR für `Runtime.evaluate()` — keine Navigation |
| macos-ax-cli | NUR für System-Scan — nicht für Klicks |

**Letztes Update**: 2026-05-05
