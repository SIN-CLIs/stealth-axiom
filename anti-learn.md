# anti-learn.md — Anti-Patterns (stealth-axiom)

> **Zweck**: Fehlermuster die NIE WIEDER auftreten dürfen.

---

## ❌ Absolute Verbote

1. **NIE webauto-nodriver** verwenden — ABSOLUT BANNED in der Stealth Suite
2. **NIE skylight-cli click** — DEPRECATED; **skylight-cli** RE-ACTIVATED für `snapshot-compact` + `batch` only
3. **NIE CDP für Navigation/Klicks** — nur JS execute/evaluate erlaubt
4. **NIE pyautogui/pynput** — Mausbewegung ist verboten
5. **NIE `pkill -f "heypiggy-bot"` oder `killall Google Chrome`** — killt ALLE Chrome-Instanzen (USER + BOT!) — nutze `SessionManager.close_all()`

## ❌ Doc-System

- **NIE** Dateien ohne W-Fragen-Kommentare erstellen
- **NIE** fehlende Pflichtdateien ignorieren — Doc-Health-Check läuft
