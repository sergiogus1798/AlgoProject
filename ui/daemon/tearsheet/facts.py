"""The Ficha's tables and bars of one sample: headline facts, rolling windows, win rate, concentration."""

import math

import pandas as pd

from core.study import blocks
from ui.daemon.tearsheet import drawdowns, months, tradestats

DENNIS = 95.0       # % of the net from the best 5 % of trades, the figure the book quotes


def _money(v: float) -> str:
    """A money figure with its cents."""
    return f"{v:.2f}"


def _share(part: int, whole: int) -> str:
    """"x % (part de whole)"."""
    return f"{100 * part / whole:.1f} % ({part} de {whole})" if whole else "—"


def _wins(pnl: pd.Series) -> tuple[str, str, str]:
    """The win-rate row with its 95 % Wilson interval."""
    if pnl.empty:
        return ("Operaciones ganadoras", "—", "La muestra no tiene operaciones.")
    wins = int((pnl > 0).sum())
    rate, low, high = tradestats.wilson(wins, len(pnl))
    return ("Operaciones ganadoras", f"{rate:.1f} % ({low:.1f} … {high:.1f})",
            f"{wins} de {len(pnl)} operaciones con P&L > 0; entre paréntesis el intervalo de "
            "Wilson al 95 % para esa cuenta.")


def headline(equity: pd.Series, pnl: pd.Series, monthly: pd.Series, sharpe: float | None,
             sample: str) -> dict:
    """The facts table: what the months, years and highs say, beside SQX's Sharpe.

    Args:
        equity: The sample's cumulative P&L per day.
        pnl: The sample's trade P&Ls.
        monthly: `months.monthly(equity)`.
        sharpe: SQX's `Sharpe Ratio [<sample>]` from metrics.parquet, None when absent.
        sample: "IS" or "OOS".

    Returns:
        A table block: medida, valor, qué cuenta.
    """
    years = months.yearly(monthly)
    flat_days, flat_from, flat_to = drawdowns.longest_flat(equity)
    first_days, first_day = drawdowns.first_high(equity)
    rows = [
        ("Meses con P&L > 0", _share(int((monthly > 0).sum()), len(monthly)),
         f"Meses naturales de la muestra con P&L positivo, sobre todos; {int((monthly == 0).sum())} "
         "meses sin ningún cambio cuentan en el total y no como positivos."),
        ("Años con P&L > 0", _share(int((years > 0).sum()), len(years)),
         "Años naturales con P&L positivo, sobre todos; el primero y el último pueden ser parciales."),
        ("Sharpe de SQX", "—" if sharpe is None or math.isnan(sharpe) else f"{sharpe:.2f}",
         f"`Sharpe Ratio [{sample}]` tal como lo exportó SQX, junto a los meses positivos para "
         "compararlos a la vista (Chan: casi todos los meses positivos va con Sharpe > 2)."),
        ("Periodo plano más largo", f"{flat_days} días ({flat_from:%Y-%m-%d} → {flat_to:%Y-%m-%d})",
         "Días naturales seguidos sin un máximo nuevo de la curva; el inicio y el final de la "
         "muestra cuentan como bordes."),
        ("Drawdown máximo anual medio", _money(drawdowns.annual_max(equity).mean()),
         "Media, sobre los años naturales, de la mayor caída de cada año bajo su propio pico "
         "dentro de ese año (dinero)."),
        ("Días hasta el primer máximo nuevo", "nunca" if first_days is None
         else f"{first_days} días ({first_day:%Y-%m-%d})",
         "Días naturales desde el primer día de la muestra hasta el primer cierre diario por "
         "encima de 0, donde empieza."),
        _wins(pnl),
        ("P&L final de la curva diaria", _money(equity.iloc[-1]),
         "Último valor de equity.parquet: lo que suman las celdas del mapa mensual."),
        ("P&L neto de las operaciones", _money(pnl.sum()),
         f"Suma de Profit/Loss de las {len(pnl)} operaciones de trades.parquet; puede no "
         "coincidir al céntimo con la curva diaria, que es otra columna de la cosecha."),
    ]
    frame = pd.DataFrame(rows, columns=["medida", "valor", "qué cuenta"])
    return blocks.table("Datos de la muestra", frame,
                        "Cada fila dice en «qué cuenta» de dónde sale su cifra.")


def windows(monthly: pd.Series) -> dict:
    """The rolling-window table: per length, how many windows and how many ended positive."""
    r = months.rolling(monthly).rename(columns={
        "months": "meses por ventana", "windows": "ventanas", "positive": "con P&L > 0",
        "share": "% con P&L > 0"})
    return blocks.table("Ventanas móviles de meses con P&L positivo", r,
                        "Todas las ventanas de meses naturales consecutivos que caben en la "
                        "muestra (una por mes de inicio), y cuántas suman P&L > 0 (tabla de "
                        "Campbell).")


def concentration(pnl: pd.Series) -> dict:
    """The best 5 % of trades' share of the net P&L, with Dennis' figure as a dashed line."""
    k, top, share = tradestats.concentration(pnl)
    note = (f"Las {k} mejores operaciones ({tradestats.TOP:.0%} de {len(pnl)}) suman "
            f"{_money(top)} de un P&L neto de {_money(pnl.sum())}. La línea discontinua en "
            f"{DENNIS:.0f} % es la cifra que cita Dennis en un libro: una referencia, no un umbral.")
    if share is None:
        note += " El neto no es positivo: la proporción no se dibuja."
    return {"kind": "bars", "title": "Peso del 5 % mejor de las operaciones en el P&L neto",
            "unit": "%", "items": [{"label": "5 % mejor", "value": share, "error": None,
                                    "state": "info"}],
            "reference": DENNIS, "note": note}
