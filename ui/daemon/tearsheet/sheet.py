"""The Ficha of one strategy as a contract result: tabs «IS» and «OOS», each computed on its own."""

import math
from datetime import datetime

import pandas as pd

from core.study import blocks, result
from ui.daemon.tearsheet import drawdowns, facts, months, tradestats

MODULE = "ui.daemon.tearsheet"
MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
SAMPLE = {"IS": "IS (build)", "OOS": "OOS (retest)", "OOS2": "OOS2 (reservado)"}


def _days(index: pd.Index) -> list[str]:
    """Days as "YYYY-MM-DD"."""
    return [f"{d:%Y-%m-%d}" for d in index]


def _line(title: str, unit: str, x: list[str], label: str, values: pd.Series, note: str) -> dict:
    """A one-series lines block, values rounded to the cent."""
    return {"kind": "lines", "title": title, "unit": unit, "x": x, "note": note,
            "series": [{"label": label, "values": values.round(2).tolist(), "role": "real"}]}


def _levels(values: list[list[float | None]]) -> list[float]:
    """Symmetric round cuts around 0 for the monthly map, 0 always a cut."""
    mags = sorted(abs(v) for row in values for v in row if v is not None)
    top = mags[int(0.95 * (len(mags) - 1))] if mags else 0.0
    if top == 0:
        return [0.0]
    base = 10 ** math.floor(math.log10(top))
    top = next(m * base for m in (1, 2, 5, 10) if m * base >= top)
    return [-top, -top / 2, -top / 4, 0.0, top / 4, top / 2, top]


def _episodes(equity: pd.Series) -> dict:
    """The five deepest drawdown episodes as a table."""
    e = drawdowns.episodes(equity)
    frame = pd.DataFrame({
        "profundidad": e["depth"].round(2),
        "pico": e["peak"].dt.strftime("%Y-%m-%d"), "valle": e["trough"].dt.strftime("%Y-%m-%d"),
        "recuperado": e["recovery"].dt.strftime("%Y-%m-%d").fillna("sin recuperar"),
        "días": e["length"], "días valle→rec.": e["recovery_days"]})
    return blocks.table("Los 5 episodios de drawdown más profundos", frame,
                        "Un episodio va del día del pico al primer día en que la curva vuelve "
                        "a él. Profundidad en dinero, pico → valle; «días», naturales, de pico "
                        "a recuperación (o al último día si no se recuperó); «días valle→rec.», "
                        "de valle a recuperación.", digits=12)


def _calendar(monthly: pd.Series) -> list[dict]:
    """The monthly heat map and the yearly bars."""
    rows, values = months.heat(monthly)
    total = float(monthly.sum())
    grid = {"kind": "grid", "title": "P&L por mes", "rows": rows, "cols": MONTHS,
            "values": values, "scale": "diverging", "levels": _levels(values),
            "labels": [["" if v is None else f"{v:.0f}" for v in r] for r in values],
            "note": f"P&L de cada mes natural (cierre del último día del mes menos el del mes "
                    f"anterior), en dinero; en blanco, meses fuera de la muestra. Las "
                    f"{len(monthly)} celdas suman {total:.2f}, el P&L final de la curva diaria."}
    years = months.yearly(monthly)
    bars = {"kind": "bars", "title": "P&L por año", "unit": "$", "reference": None,
            "items": [{"label": str(y), "value": float(v), "error": None, "state": "info"}
                      for y, v in years.items()],
            "note": "Suma de los meses de cada año natural, en dinero; el primero y el último "
                    "pueden ser años parciales."}
    return [grid, bars]


def tab(sample: str, equity: pd.Series, trades: pd.DataFrame, sharpe: float | None,
        day: str) -> dict:
    """One sample's tab.

    Args:
        sample: "IS", "OOS" or, once the door opened, "OOS2".
        equity: Its cumulative P&L per day, indexed by day, starting at 0.
        trades: Its trades, ascending in close time.
        sharpe: SQX's Sharpe of this sample.
        day: The cosecha's day, for the note.

    Returns:
        A contract tab; every figure in it counts this sample only.
    """
    x = _days(equity.index)
    capital = tradestats.capital(trades)
    money, pct = drawdowns.underwater(equity, capital)
    monthly = months.monthly(equity)
    out = [_line("P&L acumulado", "$", x, sample, equity,
                 "Curva diaria de equity.parquet: P&L cerrado acumulado desde 0 al inicio de "
                 "esta muestra."),
           _line("Bajo el agua, en dinero", "$", x, sample, money,
                 "Distancia de cada día al máximo anterior de la curva, en dinero (0 = en máximo).")]
    if pct is not None:
        out.append(_line("Bajo el agua, en % del pico de la cuenta", "%", x, sample, pct,
                         f"La misma distancia en % del saldo en el pico: capital inicial "
                         f"{capital:.0f} (saldo antes de la primera operación) más el P&L del pico."))
    out += [_episodes(equity), *_calendar(monthly),
            facts.headline(equity, trades["Profit/Loss"], monthly, sharpe, sample),
            facts.windows(monthly)]
    if len(trades):
        out.append(facts.concentration(trades["Profit/Loss"]))
    note = (f"{SAMPLE[sample]}: {x[0]} → {x[-1]}, {len(x)} días con curva y {len(trades)} "
            f"operaciones, cosecha {day}. Cada muestra empieza en 0 y se calcula sola: ninguna "
            "cifra de esta pestaña mezcla IS y OOS.")
    return result.tab(sample, SAMPLE[sample], out, note=note)


def build(data: dict) -> dict:
    """The whole Ficha of one strategy.

    Args:
        data: What `harvest.read` returned.

    Returns:
        A contract result (validated) with a tab per sample present and `harvest_day`.
    """
    tabs = []
    for s in SAMPLE:
        e = data["equity"][data["equity"]["sample"] == s]
        if e.empty:
            continue
        sharpe = data["metrics"].get(f"Sharpe Ratio [{s}]")
        tabs.append(tab(s, e.set_index("day")["equity"].astype(float),
                        data["trades"][data["trades"]["sample"] == s], sharpe, data["day"]))
    return blocks.validate({
        "module": MODULE, "strategy": data["strategy"], "identity": data["identity"],
        "computed_at": datetime.now().isoformat("T", "seconds"), "verdict": None,
        "tabs": blocks.plain(tabs), "warnings": [], "glossary": [], "harvest_day": data["day"]})
