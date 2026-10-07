"""A rule's per-timeframe / per-asset overrides (`by`) as editable rows and back, and the dialog's help texts and one-line wording."""

from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget


def by_line(key: str, passes: str, limbo: str) -> tuple[tuple, QWidget, QPushButton]:
    """The widgets of one override row: its three boxes, the row, and its «−» button."""
    boxes = tuple(QLineEdit(t) for t in (key, passes, limbo))
    for box, hint in zip(boxes, ("H4, XAUUSD, forex…", "pasa: >= 2.5", "limbo: >= 1.65")):
        box.setPlaceholderText(hint)
    drop = QPushButton("−")
    drop.setFixedWidth(40)
    line = QWidget()
    row = QHBoxLayout(line)
    row.setContentsMargins(0, 0, 0, 0)
    for box in boxes:
        row.addWidget(box)
    row.addWidget(drop)
    return boxes, line, drop


def by_rows(by: dict | None) -> list[tuple[str, str, str]]:
    """A rule's `by` as the section's rows: (key, pass, limbo)."""
    return [(k, str(v.get("pass", "")), str(v.get("limbo", ""))) for k, v in (by or {}).items()]


def by_built(rows: list[tuple[str, str, str]], old: dict | None) -> dict:
    """The rows back into `by`: no key, no row; no text, no field; other fields of an override
    survive while its key does."""
    out = {}
    for key, passes, limbo in rows:
        if key.strip():
            keep = {k: v for k, v in ((old or {}).get(key.strip()) or {}).items()
                    if k not in ("pass", "limbo")}
            out[key.strip()] = keep | {k: t.strip() for k, t in (("pass", passes), ("limbo", limbo))
                                       if t.strip()}
    return {k: v for k, v in out.items() if v}


HELP = {
    "kind": "Métrica SQX: un número que SQX calculó y el estudio copió del databank. Test de "
            "la app: un número de un estudio propio. Veredicto: un test que responde Aprobado "
            "o Suspenso. Compuesto: varias condiciones unidas por «todas» o «alguna».",
    "fact": "El dato que se mira, de los que el paso reunió en su último run del autopilot. "
            "Se puede escribir a mano la clave de uno que aún no esté en la lista.",
    "shape": "Umbral: el dato comparado con un número. Cerca de la mediana: el dato a menos "
             "de ±X % de la mediana de la población que se juzga (el databank que se corta).",
    "pass": "Lo que tiene que cumplir para pasar.",
    "limbo": "Opcional. Si no pasa pero cumple esto, queda en Limbo: sigue adelante, marcada. "
             "Vacío: no hay banda de limbo.",
    "miss": "Qué es no cumplir ni la condición ni el limbo. Fallo: la estrategia se elimina. "
            "Limbo: este criterio nunca elimina a nadie, solo marca.",
    "join": "Todas: el resultado es el de su peor condición. Alguna: el de la mejor — basta "
            "con que una pase.",
    "by": "Un umbral distinto por temporalidad (H4), activo (XAUUSD) o clase (forex); «H4+forex» "
          "exige ambas.",
    "absent": "Qué pasa si la estrategia no trae este dato. Limbo es lo que hace el juez si no se "
              "dice nada; Fallo la elimina; Pasa la deja pasar.",
    "name": "Opcional: las palabras con que la tabla nombra este criterio.",
}


KNOWN = {"name", "fact", "pass", "limbo", "else", "is", "near_median", "limbo_near_median",
         "by", "all", "any", "missing"}


def told(rule: dict) -> str:
    """A compound's part in one line, for the list; a part that is a compound is told whole."""
    if "all" in rule or "any" in rule:
        word, parts = ("Todas", rule["all"]) if "all" in rule else ("Alguna", rule["any"])
        return f"{word} de {len(parts)}:  " + "  /  ".join(told(p) for p in parts)
    test = {"pass": "Aprobado", "fail": "Suspenso"}[rule["is"]] if "is" in rule else \
        f"±{100 * rule['near_median']:g} % de la mediana" if "near_median" in rule else rule["pass"]
    return f"{rule['fact']}   {test}" + (f"   · limbo {rule['limbo']}" if "limbo" in rule else "") \
        + (f"   · sin dato: {rule['missing']}" if "missing" in rule else "")
