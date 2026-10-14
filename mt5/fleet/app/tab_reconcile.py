"""The Conciliación tab: the newest reconciled week — each live strategy against its SQX backtest, and the paired trades."""

import pandas as pd
from PySide6.QtWidgets import QVBoxLayout, QWidget

from mt5.fleet.app import fmt, read, widgets
from mt5.fleet.app.widgets import cell
from mt5.reconcile import report

LEGEND = (
    "Cada semana, el reconciliador pasa por SQX las estrategias que están en vivo, sobre la semana que acaba de "
    "terminar, y la compara con lo que la cuenta hizo de verdad. <b>No juzga</b>: cada diferencia es un número, sin "
    "listón de aprobado. <b>Emparejadas</b>: operaciones que están en los dos lados con la misma entrada dentro de "
    "la tolerancia. <b>Solo SQX / solo real</b>: operaciones sin gemela en el otro lado; una en el backtest y no en "
    "la cuenta suele ser un EA parado, o una orden que el bróker rechazó. <b>Puntos</b>: movimiento del precio en "
    "ticks, sin tamaño. <b>Divisa</b>: la de la cuenta, con el backtest puesto al tamaño de la operación real. "
    "<b>Diferencias</b>: real − SQX. <b>Reloj (h)</b>: el desfase horario entre el feed de SQX y el servidor, que "
    "el reconciliador estima. Con pocas operaciones en la semana las medias no dicen nada. Los datos de "
    "las semanas viejas están en <code>AlgoData/mt5/reconcile/&lt;semana&gt;/</code>."
)
MAX_PAIRS = 40
# The columns of `report.ROW` and `report.PAIRS` the tab shows; the rest stay in result.json and pairs.parquet.
SUMMARY = [
    "sqx_trades",
    "live_trades",
    "paired",
    "sqx_only",
    "live_only",
    "live_open",
    "clock_h",
    "entry_gap_min_mean_abs",
    "entry_slip_pts_mean",
    "pnl_gap_pts_paired",
    "pnl_gap_cur_paired",
    "mae_gap_mean",
]
PAIRED = [
    "ticket_sqx",
    "type",
    "open_sqx",
    "open_live",
    "entry_gap_min",
    "entry_slip_pts",
    "pnl_gap_pts",
    "pnl_gap_cur",
    "mae_gap",
]


def head(text: str) -> str:
    """A header over two lines where it has a parenthesis: «desfase entrada (min)»."""
    return text.replace(" (", "\n(")


def fmt_cell(value: object) -> str:
    """A figure of the reconciler's result: Spanish decimals, a dash for none."""
    if value is None or value != value:
        return fmt.DASH
    if isinstance(value, pd.Timestamp):
        return value.strftime("%d-%m %H:%M")
    if isinstance(value, pd.Timestamp):
        return value.strftime("%d-%m %H:%M")
    return fmt.money(value) if isinstance(value, float) else str(value)


class ReconcileTab(QWidget):
    """The tab's tables and the message for a week that was never reconciled."""

    def __init__(self) -> None:
        """Build the empty tab."""
        super().__init__()
        self.empty, self.head = (
            widgets.label("", "empty", True),
            widgets.label("", "section"),
        )
        columns = ["Empresa", "Estrategia", *[head(report.ROW[k]) for k in SUMMARY]]
        self.summary = widgets.table(columns, "Estrategia")
        self.pairs_head = widgets.label("Operaciones emparejadas", "section")
        self.pairs = widgets.table(
            ["Empresa", "Estrategia", *[head(report.PAIRS[k]) for k in PAIRED]],
            "Estrategia",
        )
        scroll, _ = widgets.page(
            [self.empty, self.head, self.summary, self.pairs_head, self.pairs], LEGEND
        )
        box = QVBoxLayout(self)
        box.addWidget(scroll)
        box.setContentsMargins(0, 0, 0, 0)

    def paint(self) -> None:
        """Show the newest week's result, or say there is none."""
        found = read.reconcile_result()
        self.empty.setVisible(found is None)
        self.empty.setText(
            "Aún no hay ninguna semana conciliada: el reconciliador semanal no ha corrido nunca. Para su primera "
            "semana le faltan tres cosas tuyas: el registro de magics (<code>AlgoData/mt5/reconcile/register.csv</code>: "
            "qué magic es qué estrategia en qué firma), qué cuentas están en vivo (<code>live.accounts</code>) y la "
            "tolerancia de entrada en barras (<code>pairing.entry_tolerance_bars</code>), las dos últimas en "
            "<code>mt5/reconcile/config.yaml</code>. Después: <code>python3 -m mt5.reconcile.run --week 2026-W40</code> "
            "(capítulo 89 del manual)."
        )
        for w in (self.head, self.summary, self.pairs_head, self.pairs):
            w.setVisible(found is not None)
        if found is None:
            return
        week, summary, pairs = found
        self.head.setText(f"Semana {week}")
        lines = []
        for key, s in [*summary["strategies"].items(), ("/TOTAL", summary["totals"])]:
            firm, name = key.split("/")
            lines.append(
                [cell(fmt.firm(firm), right=False), cell(name, right=False)]
                + [cell(fmt_cell(s.get(k))) for k in SUMMARY]
            )
        widgets.fill(self.summary, lines)
        shown = pairs.head(MAX_PAIRS) if pairs is not None else None
        self.pairs_head.setText(
            "Operaciones emparejadas"
            + (
                ""
                if pairs is None or len(pairs) <= MAX_PAIRS
                else f" (las primeras {MAX_PAIRS} de {len(pairs)})"
            )
        )
        widgets.fill(
            self.pairs,
            []
            if shown is None
            else [
                [
                    cell(fmt.firm(row["firm"]), right=False),  # pyright: ignore[reportArgumentType]  # pandas/numpy stubs lose the type through indexing
                    cell(row["strategy"], right=False),  # pyright: ignore[reportArgumentType]  # pandas/numpy stubs lose the type through indexing
                ]
                + [cell(fmt_cell(row[k])) for k in PAIRED]
                for _, row in shown.iterrows()
            ],
        )
