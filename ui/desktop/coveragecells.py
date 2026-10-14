"""The coverage matrix's parts that need no table: its scale and legend, the headline tiles."""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from ui.desktop.theme import C

# How much has been tried in a cell, in four steps (owner: discrete scales, with their legend).
# One hue, the accent, because it means nothing else in this window; the verdict is a mark.
LEVELS = [(0, "sin probar", C["untried"], C["muted"]), (1, "1 run", "#3a3566", "#ffffff"),
          (2, "2-3 runs", "#5c52ad", "#ffffff"), (4, "4 o más", C["accent"], "#000000")]
# The best verdict inside a cell, as a mark before its count (the ground is the amount).
MARK = {"promising": "✔ ", "weak": "~ ", "dead": "✘ "}

ACTIONS = [
    ("templates", "Ver plantillas", "Abre Plantillas con las de esta familia; si la celda ya "
                                    "tiene alguna, en la primera."),
    ("palette", "Paleta de esta familia", "Abre Paletas en la paleta por defecto de la familia: "
                                          "los bloques que el builder puede sortear."),
    ("new", "Nueva plantilla aquí", "Abre la entrevista de Nueva plantilla con la familia ya "
                                    "contestada."),
    ("research", "Investigar esta celda", "Abre el mapa de Investigar en el activo que el "
                                          "tablero del director pone primero para esta celda, "
                                          "con sus medidas."),
]
TILE_HELP = {
    "templates": "Filas de registry.csv que no están archivadas. Una plantilla es una idea, "
                 "no una estrategia y no un mercado.",
    "build_confirmed": "Cuántas han pasado de 'el XML resuelve' a 'una construcción real sacó "
                       "estrategias que llevan su bloque'. Es el único estado que prueba algo.",
    "runs": "Filas de runs.csv: cada una es una plantilla probada en un activo y un timeframe.",
    "symbols": "Activos distintos tocados por algún run.",
    "timeframes": "Timeframes distintos tocados por algún run.",
    "archetypes_used": "Familias con al menos una plantilla, sobre las siete del catálogo. "
                       "La distancia entre los dos números es de lo que tienes poco.",
    "drafts": "Briefs que el chat ha redactado y que nadie ha autorado todavía. No cuentan "
              "como plantillas: no tienen .sqx.",
}


def tile(title: str, value: str, help_key: str) -> QFrame:
    """One headline count, with the sentence that says what it counts.

    Args:
        title: The label under the number.
        value: The number, already formatted.
        help_key: Key into `TILE_HELP` for the tooltip.

    Returns:
        A framed widget. Every number in this window explains itself on hover; a count
        nobody can define is a count nobody should act on.
    """
    f = QFrame(objectName="tile")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
    f.setToolTip(TILE_HELP[help_key])
    lay = QVBoxLayout(f)
    lay.setContentsMargins(14, 10, 14, 10)
    lay.setSpacing(1)
    big = QLabel(value)
    big.setStyleSheet("font-size:22px; font-weight:600;")
    lay.addWidget(big)
    lay.addWidget(QLabel(title, objectName="faint"))  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
    return f


def level(count: int) -> tuple[int, str, str, str]:
    """The step of `LEVELS` a number of runs falls in."""
    return [step for step in LEVELS if count >= step[0]][-1]


def swatch(colour: str, text: str) -> str:
    """One square of the legend and its words, as rich text."""
    if colour == C["untried"]:           # the ground's own shade: drawn as an outline
        return f'<span style="color:{C["muted"]}; font-size:18px">□</span> {text}'
    return f'<span style="color:{colour}; font-size:18px">■</span> {text}'


def fill_tiles(tiles: QHBoxLayout, totals: dict) -> None:
    """Redraw the headline counts.

    Args:
        totals: The dict `coverage.totals` returned.
    """
    while tiles.count():
        # The last item of the row is the stretch, and a spacer has no widget: asking
        # it for one and deleting it is what made the second reload crash.
        item = tiles.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
    shown = [("Plantillas", str(totals["templates"]), "templates"),
             ("Confirmadas", str(totals["build_confirmed"]), "build_confirmed"),
             ("Runs", str(totals["runs"]), "runs"),
             ("Activos", str(totals["symbols"]), "symbols"),
             ("Timeframes", str(totals["timeframes"]), "timeframes"),
             ("Familias cubiertas",
              f"{totals['archetypes_used']}/{totals['archetypes_total']}", "archetypes_used"),
             ("Borradores", str(totals["drafts"]), "drafts")]
    for title, value, key in shown:
        tiles.addWidget(tile(title, value, key))
    tiles.addStretch()
