MICRO = {
    "classify_element": """Du bist ein AX-Tree-Analysator. Antworte mit EINEM Wort.
AX-Tree Zeile: {line}
Frage: Welche Rolle hat dieses Element?
Optionen: AXRadioButton, AXButton, AXTextField, AXCheckBox, AXStaticText, AXGroup
Antwort:""",
    "pick_answer": """Persona: {persona}
Frage: {question_text}
Optionen: {options}
Wähle die passende Antwort (nur den Text der Option):
Antwort:""",
    "verify_state": """Vor Klick: {before_state}
Nach Klick: {after_state}
Hat der Klick funktioniert? Antworte nur YES oder NO:
Antwort:""",
}

MID = {
    "classify_page": """Analysiere diesen AX-Tree-Ausschnitt und klassifiziere die Seite:
{ax_tree_snippet}

Kategorien:
- consent (Zustimmung erforderlich)
- login (Anmeldung)
- question_radio (Frage mit Radio-Buttons)
- question_checkbox (Frage mit Checkboxen)
- question_text (Texteingabe)
- question_math (Mathe-Aufgabe)
- question_image (Bild-Frage)
- question_video (Video-Frage)
- finished (Umfrage beendet)
- unknown

Antworte mit der Kategorie und Begründung:""",
    "plan_next_action": """Aktueller Umfrage-Status:
- Letzte Frage: {last_question}
- Gegebene Antwort: {last_answer}
- Seite enthält: {available_elements}

Was ist der nächste Schritt?
1. Klicke "Weiter"
2. Warte auf neue Seite (polling)
3. Umfrage beendet
4. Fehler – neu analysieren

Antworte mit Nummer und kurzer Begründung:""",
}

HEAVY = {
    "analyze_new_provider": """Unbekannter Umfrage-Anbieter erkannt.
AX-Tree der Startseite: {ax_tree}
Body-Text: {body_text}

Analysiere:
1. Wie ist die Navigation? (Buttons, Links, Seiten-Struktur)
2. Wie sind Fragen aufgebaut? (Matrix, Einzelfragen, Slider?)
3. Wie wird "Weiter" signalisiert?
4. Gibt es Fallstricke? (Consent, Login, Captcha?)

Erstelle eine Schritt-für-Schritt-Strategie:""",
}

def get_prompt(task_type: str, tier: str, **kwargs) -> str:
    pool = {"micro": MICRO, "mid": MID, "heavy": HEAVY}.get(tier, MID)
    template = pool.get(task_type)
    if not template:
        return ""
    return template.format(**kwargs)
