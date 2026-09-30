"""Drawing helpers for Verificar: the firm's light widget, the past-runs table, result filtering."""
import copy

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QCheckBox, QTableWidget, QTableWidgetItem

from ui.desktop.blocks.states import colour
from ui.desktop.theme import T

# (header, tooltip) of the list of checks.
COLUMNS = (("Cuándo", "Cuándo empezó la verificación."),
           ("Resultado", "Por empresa: ✓ Validada, ✗ No validada, — no se pudo verificar."),
           ("Estrategia", "La estrategia verificada."),
           ("Activo", "Su activo y timeframe."),
           ("Ventana", "Los días backtesteados en los dos lados."),
           ("Modelo", "El modelo del tester de MT5."),
           ("Estado", "En marcha, hecha o fallida, y por qué falló."))
MARKS = {"pass": "✓", "fail": "✗"}


class FirmLight(QCheckBox):
    """A small square with a light: on in green when the firm is active, off in grey."""

    def __init__(self, firm: str, label: str) -> None:
        """Args: firm: the key, e.g. "ftmo". label: how the owner reads it, e.g. "FTMO"."""
        super().__init__(label)
        self.firm = firm
        on, off = colour("pass"), T["faint"]
        self.setStyleSheet(
            f"QCheckBox::indicator {{ width: 14px; height: 14px; border-radius: 3px; "
            f"border: 1px solid {T['line']}; background: {off}; }}"
            f"QCheckBox::indicator:checked {{ background: {on}; border-color: {on}; }}")


def header(table: QTableWidget) -> None:
    """Fill the past-runs table's header cells, with their tooltips."""
    for i, (head, tip) in enumerate(COLUMNS):
        item = QTableWidgetItem(head)
        item.setToolTip(tip)
        table.setHorizontalHeaderItem(i, item)


def fill_runs(table: QTableWidget, runs: list[dict]) -> None:
    """One row per past check, newest first — `runs` is already sorted that way."""
    table.setRowCount(len(runs))
    for r, run in enumerate(runs):
        firms = [f"{f} {MARKS.get(s, '?')}" for f, s in (run.get("firms") or {}).items()]
        firms += [f"{f} —" for f in run.get("refused") or {}]
        state = {"running": "en marcha", "done": "hecha", "failed": "fallida"}.get(
            run.get("state"), run.get("state") or "")
        cells = [run.get("started", "")[:16].replace("T", " "), " · ".join(firms),
                 run.get("strategy", ""), f"{run.get('asset', '')} {run.get('timeframe', '')}",
                 f"{run.get('from', '')} → {run.get('to', '')}", run.get("model", ""),
                 state + (f": {run['error']}" if run.get("error") else "")]
        for c, value in enumerate(cells):
            item = QTableWidgetItem(value)
            if c == 1 and run.get("verdict") in ("pass", "fail"):
                item.setForeground(Qt.GlobalColor.white)
                item.setBackground(QColor(colour(run["verdict"])))
            item.setToolTip(value)
            table.setItem(r, c, item)
    table.resizeColumnsToContents()


def filtered(result: dict, active: set[str]) -> dict:
    """A copy of a study result with every other firm's blocks, series and columns dropped.

    Args:
        result: The full study contract, every firm's data included (§3.7's data cost is
            paid once, at run time — this only changes what is drawn).
        active: The firm keys whose light is on.

    Returns:
        A deep copy: `result` itself is never mutated, so toggling twice still shows everything.
    """
    out = copy.deepcopy(result)
    for tab in out.get("tabs", []):
        kept = []
        for block in tab.get("blocks", []):
            firm = block.get("firm")
            if firm is not None and firm not in active:
                continue
            if block["kind"] == "lines":
                block["series"] = [s for s in block["series"]
                                   if s.get("firm") is None or s.get("firm") in active]
            cols = block.get("firm_columns")
            if cols:
                drop = {j for f, i in cols.items() if f not in active       # one or a list
                        for j in (i if isinstance(i, list) else [i])}
                block["columns"] = [c for i, c in enumerate(block["columns"]) if i not in drop]
                block["align"] = [a for i, a in enumerate(block["align"]) if i not in drop]
                block["rows"] = [[v for i, v in enumerate(row) if i not in drop]
                                 for row in block["rows"]]
            kept.append(block)
        tab["blocks"] = kept
    return out
