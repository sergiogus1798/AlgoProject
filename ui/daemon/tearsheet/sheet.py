"""The Ficha of one strategy as a contract result: tabs «IS» and «OOS», each computed on its own."""

from datetime import datetime
from pathlib import Path

import pandas as pd

from core.study import blocks, result
from ui.daemon.strategy import costcurve
from ui.daemon.tearsheet import drawdowns, months, pnl, tradestats

MODULE = "ui.daemon.tearsheet"
SAMPLE = {"IS": "IS (build)", "OOS": "OOS (retest)", "OOS2": "OOS2"}
INK = {"IS": "IS", "OOS": "OOS", "OOS2": "OOS"}       # `blocks.states.CURVE`'s tone per sample
UNITS = ("%", "$")                                   # the drawdown's two readings, % first


def _days(index: pd.Index) -> list[str]:
    """Days as "YYYY-MM-DD"."""
    return [f"{d:%Y-%m-%d}" for d in index]


def _pnl(sample: str, equity: pd.Series, trades: pd.DataFrame, repriced: pd.DataFrame | None,
         top: float) -> dict:
    """«P&L acumulado»: SQX's curve and the real one, dashed without their best `top` %."""
    got = pnl.curves(equity, trades, repriced, top)
    ink = INK[sample]
    names = {"sqx": ("SQX", "sqx"), "real": ("spread y slippage reales", "real"),
             "sqx_top": (f"SQX sin el top {top:g} %", "sqx"),
             "real_top": (f"spread y slippage reales sin el top {top:g} %", "real")}
    series = [{"label": f"{names[k][0]} · {sample}", "values": v.round(2).tolist(), "role": "real",
               "ink": f"{names[k][1]}.{ink}", "dash": k.endswith("_top")} for k, v in got.items()]
    note = ("Curva diaria de equity.parquet: P&L cerrado acumulado desde 0 al inicio de esta "
            "muestra. " + ("La de spread y slippage reales es la misma corregida, el día que "
                           "cierra cada operación, por lo que cambian los costes de Darwinex "
                           "(estudio spread). " if "real" in got else
                           "Sin informe del estudio spread: sólo la de SQX. ")
            + (f"Discontinuas: cada curva sin su {top:g} % de operaciones mejores (al menos "
               "una), ordenadas por su propio P&L." if top else ""))
    return {"kind": "lines", "title": "P&L acumulado", "unit": "$",
            "x": _days(got["sqx"].index), "series": series, "note": note}


def _drawdown(sample: str, equity: pd.Series, trades: pd.DataFrame, unit: str) -> dict:
    """«Drawdown»: the distance of SQX's daily curve below its running peak, in % or in $."""
    capital = tradestats.capital(trades)
    money, pct = drawdowns.underwater(equity, capital)
    shown, unit = (pct, "%") if unit == "%" and pct is not None else (money, "$")
    worst = shown.idxmin()
    how = (f"en % del saldo en el pico: capital inicial {capital:.0f} (saldo antes de la primera "
           "operación) más el P&L del pico" if unit == "%" else "en dinero")
    return {"kind": "lines", "title": "Drawdown", "unit": unit, "x": _days(equity.index),
            "series": [{"label": f"drawdown · {sample}", "values": shown.round(2).tolist(),
                        "role": "real", "ink": f"sqx.{INK[sample]}"}],
            "note": f"Distancia de cada día al máximo anterior de la curva diaria de SQX, {how}. "
                    f"Máximo: {shown.min():.2f} {unit} el {worst:%Y-%m-%d}."}


def _years(sample: str, equity: pd.Series) -> dict:
    """«P&L por año»: one column per calendar year of SQX's daily curve."""
    years = months.yearly(months.monthly(equity))
    return {"kind": "bars", "title": "P&L por año", "unit": "$", "reference": None,
            "vertical": True,
            "items": [{"label": str(y), "value": float(v), "error": None, "state": "info",
                       "ink": f"sqx.{INK[sample]}"} for y, v in years.items()],
            "note": "Suma de los meses de cada año natural de la curva diaria de SQX, en "
                    "dinero; el primero y el último pueden ser años parciales."}


def tab(sample: str, equity: pd.Series, trades: pd.DataFrame, repriced: pd.DataFrame | None,
        day: str, top: float, dd: str) -> dict:
    """One sample's tab.

    Args:
        sample: "IS", "OOS" or, once the door opened, "OOS2".
        equity: Its cumulative P&L per day, indexed by day, starting at 0.
        trades: Its trades, ascending in close time.
        repriced: Its rows of the `spread` report, None without one.
        day: The cosecha's day, for the note.
        top: Percent of the best trades the P&L also draws without; 0 for none.
        dd: The drawdown's unit, "%" or "$".

    Returns:
        A contract tab; every figure in it counts this sample only.
    """
    x = _days(equity.index)
    out = [_pnl(sample, equity, trades, repriced, top), _drawdown(sample, equity, trades, dd),
           _years(sample, equity)]
    note = (f"{SAMPLE[sample]}: {x[0]} → {x[-1]}, {len(x)} días con curva y {len(trades)} "
            f"operaciones, cosecha {day}. Cada muestra empieza en 0 y se calcula sola: ninguna "
            "cifra de esta pestaña mezcla IS y OOS.")
    return result.tab(sample, SAMPLE[sample], out, note=note)


def build(data: dict, spread: list[Path] = (), top: float = 0.0, dd: str = "%") -> dict:
    """The whole Ficha of one strategy.

    Args:
        data: What `harvest.read` returned.
        spread: Its `spread` report folders, newest first; none draws SQX's curve alone.
        top: Percent of the best trades the P&L also draws without; 0 for none.
        dd: The drawdown's unit, "%" or "$".

    Returns:
        A contract result (validated) with a tab per sample present and `harvest_day`.
    """
    found = costcurve.repriced(spread, data["strategy"], data["identity"]) if spread else None
    tabs = []
    for s in SAMPLE:
        e = data["equity"][data["equity"]["sample"] == s]
        if e.empty:
            continue
        rows = None if found is None else found[0][found[0]["sample"] == s]
        tabs.append(tab(s, e.set_index("day")["equity"].astype(float),
                        data["trades"][data["trades"]["sample"] == s], rows, data["day"], top, dd))
    return blocks.validate({
        "module": MODULE, "strategy": data["strategy"], "identity": data["identity"],
        "computed_at": datetime.now().isoformat("T", "seconds"), "verdict": None,
        "tabs": blocks.plain(tabs), "warnings": [], "glossary": [], "harvest_day": data["day"]})
