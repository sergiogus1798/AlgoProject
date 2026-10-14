"""The Ficha of one strategy as a contract result: tabs «IS» and «OOS», each computed on its own."""

from datetime import datetime
from typing import Any

import pandas as pd

from core.study import blocks, result
from ui.daemon.tearsheet import drawdowns, months, pnl, tradestats

MODULE = "ui.daemon.tearsheet"
SAMPLE = {"IS": "IS (build)", "OOS": "OOS (retest)", "OOS2": "OOS2"}
INK = {
    "IS": "IS",
    "OOS": "OOS",
    "OOS2": "OOS",
}  # `blocks.states.CURVE`'s tone per sample
UNITS = ("%", "$")  # the drawdown's two readings, % first


def _days(index: pd.Index) -> list[str]:
    """Days as "YYYY-MM-DD"."""
    return [f"{d:%Y-%m-%d}" for d in index]


def _pnl(
    sample: str, equity: pd.Series, trades: pd.DataFrame, top: float
) -> dict[str, Any]:
    """«P&L acumulado»: SQX's curve, dashed without its best `top` %."""
    got = pnl.curves(equity, trades, top)
    ink = INK[sample]
    names = {"sqx": "SQX", "sqx_top": f"SQX sin el top {top:g} %"}
    series = [
        {
            "label": f"{names[k]} · {sample}",
            "values": v.round(2).tolist(),
            "role": "real",
            "ink": f"sqx.{ink}",
            "dash": k.endswith("_top"),
        }
        for k, v in got.items()
    ]
    note = (
        "Curva diaria de equity.parquet: P&L cerrado acumulado desde 0 al inicio de esta "
        "muestra. "
        + (
            f"Discontinua: la curva sin su {top:g} % de operaciones mejores (al menos "
            "una)."
            if top
            else ""
        )
    )
    return {
        "kind": "lines",
        "title": "P&L acumulado",
        "unit": "$",
        "x": _days(got["sqx"].index),
        "series": series,
        "note": note,
    }


def _drawdown(
    sample: str, equity: pd.Series, trades: pd.DataFrame, unit: str
) -> dict[str, Any]:
    """«Drawdown»: the distance of SQX's daily curve below its running peak, in % or in $."""
    capital = tradestats.capital(trades)
    money, pct = drawdowns.underwater(equity, capital)
    shown, unit = (pct, "%") if unit == "%" and pct is not None else (money, "$")
    worst = shown.idxmin()
    how = (
        f"en % del saldo en el pico: capital inicial {capital:.0f} (saldo antes de la primera "
        "operación) más el P&L del pico"
        if unit == "%"
        else "en dinero"
    )
    return {
        "kind": "lines",
        "title": "Drawdown",
        "unit": unit,
        "x": _days(equity.index),
        "series": [
            {
                "label": f"drawdown · {sample}",
                "values": shown.round(2).tolist(),
                "role": "real",
                "ink": f"sqx.{INK[sample]}",
            }
        ],
        "note": f"Distancia de cada día al máximo anterior de la curva diaria de SQX, {how}. "
        f"Máximo: {shown.min():.2f} {unit} el {worst:%Y-%m-%d}.",
    }


def _years(sample: str, equity: pd.Series) -> dict[str, Any]:
    """«P&L por año»: one column per calendar year of SQX's daily curve."""
    years = months.yearly(months.monthly(equity))
    return {
        "kind": "bars",
        "title": "P&L por año",
        "unit": "$",
        "reference": None,
        "vertical": True,
        "items": [
            {
                "label": str(y),
                "value": float(v),
                "error": None,
                "state": "info",
                "ink": f"sqx.{INK[sample]}",
            }
            for y, v in years.items()
        ],
        "note": "Suma de los meses de cada año natural de la curva diaria de SQX, en "
        "dinero; el primero y el último pueden ser años parciales.",
    }


def tab(
    sample: str, equity: pd.Series, trades: pd.DataFrame, day: str, top: float, dd: str
) -> dict[str, Any]:
    """One sample's tab.

    Args:
        sample: "IS", "OOS" or, once the door opened, "OOS2".
        equity: Its cumulative P&L per day, indexed by day, starting at 0.
        trades: Its trades, ascending in close time.
        day: The cosecha's day, for the note.
        top: Percent of the best trades the P&L also draws without; 0 for none.
        dd: The drawdown's unit, "%" or "$".

    Returns:
        A contract tab; every figure in it counts this sample only.
    """
    x = _days(equity.index)
    out = [
        _pnl(sample, equity, trades, top),
        _drawdown(sample, equity, trades, dd),
        _years(sample, equity),
    ]
    note = (
        f"{SAMPLE[sample]}: {x[0]} → {x[-1]}, {len(x)} días con curva y {len(trades)} "
        f"operaciones, cosecha {day}. Cada muestra empieza en 0 y se calcula sola: ninguna "
        "cifra de esta pestaña mezcla IS y OOS."
    )
    return result.tab(sample, SAMPLE[sample], out, note=note)


def build(data: dict, top: float = 0.0, dd: str = "%") -> dict[str, Any]:
    """The whole Ficha of one strategy.

    Args:
        data: What `harvest.read` returned.
        top: Percent of the best trades the P&L also draws without; 0 for none.
        dd: The drawdown's unit, "%" or "$".

    Returns:
        A contract result (validated) with a tab per sample present and `harvest_day`.
    """
    tabs = []
    for s in SAMPLE:
        e = data["equity"][data["equity"]["sample"] == s]
        if e.empty:
            continue
        tabs.append(
            tab(
                s,
                e.set_index("day")["equity"].astype(float),
                data["trades"][data["trades"]["sample"] == s],
                data["day"],
                top,
                dd,
            )
        )
    return blocks.validate(
        {
            "module": MODULE,
            "strategy": data["strategy"],
            "identity": data["identity"],
            "computed_at": datetime.now().isoformat("T", "seconds"),
            "verdict": None,
            "tabs": blocks.plain(tabs),
            "warnings": [],
            "glossary": [],
            "harvest_day": data["day"],
        }
    )
