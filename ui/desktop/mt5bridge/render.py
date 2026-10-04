"""Drawing helpers for Verificar: the firm's light widget, the past-runs table, result filtering."""
import copy
from html import escape

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QAbstractItemView, QCheckBox, QTableWidget, QTableWidgetItem

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
LEGEND = ("Resultado, por empresa: ✓ validada · ✗ no validada · — no se pudo verificar. Verde: "
          "todas las empresas la validan · ámbar: sólo alguna · rojo: ninguna, o la "
          "verificación falló antes de comparar.")
NAMES = {"ftmo": "FTMO", "hantec": "Hantec"}      # as the owner writes them (2026-09-29 §3.3)


def name(firm: str) -> str:
    """A firm's key as the owner reads it: FTMO in capitals, Hantec with a capital H."""
    return NAMES.get(firm, firm.capitalize())


TICKS_HELP = (
    "Además del modelo elegido arriba, el EA se backtestea una segunda vez en «Every tick based "
    "on real ticks»: los ticks históricos reales del bróker, con su spread real — la ejecución "
    "más fiel que da MT5. («Every tick» a secas interpola ticks sintéticos desde las barras M1, "
    "así que no aporta fidelidad sobre OHLC M1.)\n\n"
    "El gráfico dibuja tres curvas por empresa — SQX, MT5 en el modelo elegido y MT5 en Real "
    "ticks — y los cinco criterios se juzgan dos veces, una por pasada. El veredicto que entra "
    "en el pool sigue siendo el del modelo elegido; el de Real ticks sale al lado.\n\n"
    "Es mucho más lento: puede tardar horas por empresa (tope de 240 min por pasada). Si el "
    "modelo elegido ya es real_ticks, la casilla no hace nada: no se corre dos veces.")


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


def runs_table() -> QTableWidget:
    """The past-runs table, empty: one selectable row per check, headers with their tooltips."""
    table = QTableWidget(0, len(COLUMNS))
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.verticalHeader().hide()
    for i, (head, tip) in enumerate(COLUMNS):
        item = QTableWidgetItem(head)
        item.setToolTip(tip)
        table.setHorizontalHeaderItem(i, item)
    table.horizontalHeader().setStretchLastSection(True)
    return table


def no_result(meta: dict) -> str:
    """What stands where a check's result would be: why it failed, or that it still runs."""
    if not meta.get("error"):
        return "En marcha: todavía no hay resultado que enseñar."
    return (f"<span style='color: {colour('fail')};'><b>La verificación falló antes de "
            f"comparar.</b></span><br>" + escape(meta["error"]).replace("\n", "<br>"))


def short(why: str, limit: int = 70) -> str:
    """A run's state as one cell: its first line, cut — the whole of it is the cell's tooltip.

    A builder's refusal runs to several lines and made the table scroll sideways, hiding
    every column after it.
    """
    line = why.splitlines()[0] if why else ""
    return line if len(line) <= limit and line == why else line[:limit].rstrip() + "…"


def fill_runs(table: QTableWidget, runs: list[dict]) -> None:
    """One row per past check, newest first — `runs` is already sorted that way."""
    table.setRowCount(len(runs))
    for r, run in enumerate(runs):
        firms = [f"{name(f)} {MARKS.get(s, '?')}" for f, s in (run.get("firms") or {}).items()]
        firms += [f"{name(f)} —" for f in run.get("refused") or {}]
        state = {"running": "en marcha", "done": "hecha", "failed": "fallida"}.get(
            run.get("state"), run.get("state") or "")
        failed = run.get("state") == "failed"
        why = state + (f": {run['error']}" if run.get("error") else "")
        cells = [run.get("started", "")[:16].replace("T", " "),
                 "Falló" if failed and not firms else " · ".join(firms),
                 run.get("strategy", ""), f"{run.get('asset', '')} {run.get('timeframe', '')}",
                 f"{run.get('from', '')} → {run.get('to', '')}",
                 run.get("model", "") + (" + Real ticks" if run.get("ticks") else ""),
                 short(why)]
        verdict = "fail" if failed else run.get("verdict")
        for c, value in enumerate(cells):
            item = QTableWidgetItem(value)
            if c == 1 and verdict in ("pass", "watch", "fail"):   # watch: some firms
                item.setForeground(Qt.GlobalColor.white)
                item.setBackground(QColor(colour(verdict)))
            item.setToolTip(why if c == len(cells) - 1 else value)
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
