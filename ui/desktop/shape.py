"""The panel that says which parts of a template the builder fills, and which a palette reaches."""

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from ui.desktop.theme import C, chip


def shape_panel(t: dict) -> QFrame:
    """One template's holes and fixed blocks, hole by hole.

    Args:
        t: The template record from the daemon, carrying `holes`, `fixed` and `reach`.

    Returns:
        A framed block for the template's page. This is what stops the palette view being a
        lie: a palette narrows a free hole and nothing else, so a template whose holes are
        all bound to groups has to say so here instead of looking configurable.
    """
    f = QFrame(objectName="panel")
    lay = QVBoxLayout(f)
    lay.setContentsMargins(14, 12, 14, 12)
    lay.setSpacing(6)
    free = [h for h in t["holes"] if not h["group"]]
    verdict = QLabel(t["reach"])
    verdict.setWordWrap(True)
    verdict.setStyleSheet(f"color:{C['promising'] if free else C['weak']};")
    lay.addWidget(verdict)
    for h in t["holes"]:
        where = (chip("libre — la paleta lo gobierna", C["promising"]) if not h["group"]
                 else chip(f"atado a {h['group']}", C["weak"]))
        if h["unknown_group"]:
            where = chip("atado a un grupo que esta instalación no tiene", C["dead"])
        lay.addWidget(QLabel(f'<b>{h["id"]}</b> ({h["kind"]})  {where}'))
    if t["fixed"]:
        fixed = QLabel("Fijos en la plantilla, fuera de toda paleta: "
                       + ", ".join(t["fixed"]))
        fixed.setWordWrap(True)
        fixed.setStyleSheet(f"color:{C['muted']};")
        lay.addWidget(fixed)
    return f
