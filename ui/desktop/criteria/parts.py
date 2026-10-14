"""What the Criterios zone is made of: its sentences, the «?» mark and the table of rules."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QLabel, QTableWidget, QTableWidgetItem

from ui.desktop.criteria.overrides import HELP
from ui.desktop.theme import C

COLUMNS = ("Criterio", "Tipo", "Condición", "Limbo", "Excepciones")
OUTCOMES = ("Cada criterio da a cada estrategia uno de tres resultados. Pasa: cumple la "
            "condición. Limbo: no la cumple pero entra en la banda de limbo — sigue adelante, "
            "marcada. Fallo: ni una ni otra — se elimina. El resultado de una estrategia en "
            "un paso es el de su PEOR criterio, y un criterio cuyo dato falta es Limbo.")
TIPS = {
    "Criterio": "El dato que se mira. Al pasar el ratón: su clave en el fichero y lo que "
                "criteria.yaml dice de la regla.",
    "Tipo": HELP["kind"],
    "Condición": "Lo que tiene que cumplir para pasar. " + HELP["shape"],
    "Limbo": "La banda intermedia: no pasa, pero tampoco se elimina. «—»: no hay banda, no "
             "pasar es Fallo. «Si no cumple»: este criterio nunca elimina, solo marca.",
    "Excepciones": "Umbrales distintos según lo que es el proyecto: su timeframe, su activo "
                   "o su clase (forex, no_forex). Manda la primera excepción que encaja.",
}
CUT = ("El databank de SQX donde se aplica el veredicto del paso: de él se quitan las "
       "estrategias con Fallo, y es el que lee la tarea siguiente.")
INTRO = ("Lo que tiene que cumplir una estrategia en cada paso para pasar sola al siguiente. "
         "Juzga el autopilot; los filtros del Build (paso 6) son los únicos que aplica SQX. "
         "Doble clic en un criterio para cambiarlo o borrarlo.")
FREEZE = ("Bloquea los criterios: a partir de ahí esta pestaña solo se lee y dice desde "
          "cuándo. Un umbral movido después de ver resultados es la forma más barata de "
          "sobreajustar; congelar deja constancia de que no se movieron. No se puede "
          "descongelar desde la ventana.")


def mark(text: str) -> QLabel:
    """A round «?» whose tooltip explains what stands beside it."""
    label = QLabel("?", objectName="helpmark")  # pyright: ignore[reportCallIssue]  # PySide6 stub lacks property kwargs
    label.setFixedSize(17, 17)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setCursor(Qt.CursorShape.WhatsThisCursor)
    label.setToolTip(text)
    return label


def table(columns: tuple, rows: list[list[tuple[str, str]]], tips: dict) -> QTableWidget:
    """A read-only table as tall as its rows.

    Args:
        columns: The headers.
        rows: Per row, one (text, tooltip) per column.
        tips: Header → its tooltip.
    """
    t = QTableWidget(len(rows), len(columns))
    t.setHorizontalHeaderLabels(columns)
    t.verticalHeader().setVisible(False)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    t.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    t.setWordWrap(False)          # a long cell is cut with «…»; its tooltip says all of it
    colours = {"Condición": C["promising"], "Limbo": C["weak"]}
    for c, name in enumerate(columns):
        head = t.horizontalHeaderItem(c)
        if head is not None:
            head.setToolTip(tips.get(name, ""))
        t.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        for r, row in enumerate(rows):
            item = QTableWidgetItem(row[c][0])
            item.setToolTip(row[c][1])
            if name in colours and row[c][0] != "—":
                item.setForeground(QColor(colours[name]))
            t.setItem(r, c, item)
    t.horizontalHeader().setStretchLastSection(True)
    t.resizeRowsToContents()      # a compound says one condition per line
    t.setFixedHeight(t.horizontalHeader().sizeHint().height() + 2
                     + sum(t.rowHeight(r) for r in range(len(rows))))
    return t


def cells(row: dict) -> list[tuple[str, str]]:
    """One rule, or one Build filter, as the five cells of its row."""
    why = f"{row['tip']}\n\n{row['why']}" if row.get("why") and "rule" in row else row["tip"]
    return [(row["label"], why), (row["kind"], TIPS["Tipo"]), (row["passes"], row["passes"]),
            (row["limbo"], TIPS["Limbo"]),
            (row["by"] or "—", row.get("why", "") if "rule" not in row else row["by"])]
