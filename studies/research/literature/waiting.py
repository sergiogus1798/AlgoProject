"""The queue: each scout entry and whether the market profile has measured it yet."""

import pandas as pd

from studies.research.literature import selection

QUESTION, NO_MEASURE, WAITING, MEASURED = ("pregunta al dueño", "sin medida: falta una condición",
                                           "en cola", "medida")


def tested(entry: dict) -> list[str]:
    """The measures that test an entry: its own, and the existing ones stating the same rule."""
    tr = entry["translation"]
    return [s["name"] for s in tr.get("measures", [])] + tr.get("tested_by", [])


def state(entry: dict, measured: set[str]) -> str:
    """Where an entry stands: an open question, no measure written, waiting, or measured."""
    question = entry.get("question")
    if question and not question["answer"]:
        return QUESTION
    names = tested(entry)
    if not names:
        return NO_MEASURE
    return MEASURED if set(names) <= measured else WAITING


def reading(rows: pd.DataFrame) -> str:
    """What the profile measured for one entry on `build`, in one Spanish phrase."""
    ran = pd.DataFrame(rows[rows["n_trades"] >= 30])
    if ran.empty:
        return f"{len(rows)} celdas, ninguna llega a 30 operaciones en build"
    best = ran.sort_values(["passes", "q", "multiple"], ascending=[False, True, False]).iloc[0]
    tried = f"{rows['measure'].nunique()} medidas, " if rows["measure"].nunique() > 1 else ""
    return (f"{tried}{len(ran)} celdas con contraste, {int((ran['p'] <= 0.05).sum())} con p cruda ≤ 0,05, "
            f"{int(ran['significant'].sum())} significativas tras corregir, "
            f"{int(ran['passes'].sum())} pasan los cuatro filtros; mejor: `{best['measure']}` {best['symbol']} "
            f"{best['timeframe']} {best['direction']} {best['multiple']:.1f}× el coste, "
            f"p corr. {best['q']:.2f}, {best['trades_per_year']:.0f} op/año")


def table(entries: list[dict], measures: pd.DataFrame, classes: dict) -> list[dict]:
    """One row per scout entry: its state, and what was measured where it applies.

    Args:
        entries: The scout's entries (the hand-built file is read by the profile's bibliography).
        measures: The profile's `measures.csv`.
        classes: Asset class → symbols, from the config.

    Returns:
        `id`, `family`, `state`, `measures`, `symbols`, `reading`, `passing` — the cells
        (symbol, timeframe, direction, measure) where a measure of the entry passes the four
        filters.
    """
    measured, out = set(measures["measure"]), []
    for e in entries:
        where = selection.symbols(e, classes)
        got = state(e, measured)
        names = tested(e)
        rows = measures[measures["measure"].isin(names) & measures["symbol"].isin(where)]
        passing = rows[rows["passes"]]
        out.append({"id": e["id"], "family": e["family"], "state": got, "measures": names,
                    "symbols": where, "reading": reading(pd.DataFrame(rows)) if got == MEASURED else "—",
                    "passing": list(zip(passing["symbol"], passing["timeframe"],
                                        passing["direction"], passing["measure"]))})
    return out
