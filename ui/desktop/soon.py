"""The page a zone shows before it is built: what goes there, and how it is done today."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from ui.desktop.theme import C, chip

# One entry per zone of the unified platform that has no view yet. `today` is the honest
# half: a page that only promised something would be an advert, and the reader needs to
# know what to open meanwhile. Sources: the six zones of
# docs/AgentPDFs/plataforma-unificada-2026-09-20.md §10 and the steps of WORKFLOW.md.
ZONES = {
    "Datos": {
        "steps": "antes del paso 1",
        "what": "El catálogo de AlgoData: qué exports existen, de qué fecha son, cuánto ocupan "
                "y cuáles están rancios — con la librería de barras al lado, que es el único "
                "dato que se guarda de verdad.",
        "today": "Leer a mano ~/Desktop/AlgoData/INDEX.md, y correr python3 -m core.barstore "
                 "cuando hay dudas de si las velas están al día.",
    },
    "Estudios": {
        "steps": "pasos 8, 10, 12, 14, 16, 17 y 18",
        "what": "Monte Carlo, Retest, Cross-market y Cross-timeframe como pestañas de UNA vista, "
                "compartiendo la estrategia seleccionada, los filtros y la escala de color. "
                "Que dejen de ser cuatro aplicaciones es el motivo de que exista el demonio.",
        "today": "Tres serve.py distintos en strategies/*/explorer/, cada uno con su puerto y su "
                 "pestaña de navegador, sin estado compartido entre ellos.",
    },
    "Carteras": {
        "steps": "después del 20",
        "what": "Composición de una cartera, correlaciones entre sus estrategias y riesgo "
                "agregado.",
        "today": "Nada: portfolio/ está vacío. Es la zona que menos existe de las cinco.",
    },
}


CARD_WIDTH = 760
TEXT_WIDTH = CARD_WIDTH - 48   # the card's fixed width less its horizontal margins


def wrapped(text: str, colour: str, faint: bool = False) -> QLabel:
    """A paragraph that really occupies the height its wrapping needs.

    Args:
        text: The paragraph.
        colour: Hex colour for the text.
        faint: True for the small print.

    Returns:
        A label whose minimum height is asked of `heightForWidth` explicitly. A wrapped
        QLabel reports a one-line sizeHint and a layout believes it, which clips the
        paragraph to two lines — so the height is computed here rather than guessed.
    """
    label = QLabel(text)
    label.setWordWrap(True)
    if faint:
        label.setObjectName("faint")
    label.setStyleSheet(f"color:{colour};")
    label.setFixedWidth(TEXT_WIDTH)
    label.setMinimumHeight(label.heightForWidth(TEXT_WIDTH))
    return label


def page(name: str) -> QWidget:
    """The whole page for one unbuilt zone.

    Args:
        name: Zone name, a key of `ZONES`.

    Returns:
        A widget saying what will live here, how the job is done today, and which steps of
        the workflow it covers. It is clickable and reachable on purpose: five dead entries
        in the sidebar explain nothing, and a disabled button in Qt never shows its tooltip.
    """
    zone = ZONES[name]
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(14)
    lay.addWidget(QLabel(name, objectName="h1"))

    card = QFrame(objectName="panel")
    inner = QVBoxLayout(card)
    inner.setContentsMargins(24, 22, 24, 24)
    inner.setSpacing(14)
    inner.addWidget(QLabel(chip("todavía no", C["weak"])
                           + "  " + chip(zone["steps"], C["muted"])))

    for title, body in (("Qué irá aquí", zone["what"]), ("Cómo se hace hoy", zone["today"])):
        head = QLabel(title, objectName="h2")
        inner.addWidget(head)
        inner.addWidget(wrapped(body, C["muted"]))

    inner.addWidget(wrapped("Esta entrega es solo el módulo de plantillas. Las zonas llegan como "
                            "una vista más de esta misma ventana, nunca como una segunda "
                            "aplicación.", C["faint"], faint=True))
    # Fixed and not maximum: a word-wrapped QLabel can only compute its height against a
    # width the layout already knows, and a card left to its own sizeHint clips the text.
    card.setFixedWidth(CARD_WIDTH)

    lay.addWidget(card, 0, Qt.AlignLeft)
    lay.addStretch()
    return w
