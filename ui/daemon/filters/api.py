"""The filter routes: metrics offered, apply, manual discard, clear, state, and saved filters."""

import re
from collections.abc import Callable

from fastapi import APIRouter
from pydantic import BaseModel

from ui.daemon.databank import table as tablemod
from ui.daemon.filters import discards, dists, evaluate, ledgerrow, saved
from ui.daemon.runner import where

ROUTER = APIRouter()


class Row(BaseModel):
    """One condition: a metric, an operator and its value (two numbers for «entre»)."""

    metric: str
    op: str
    value: float | str | list[float]


class Apply(BaseModel):
    """A filter on one databank: its rows, combined with AND (Q15: AND only)."""

    project: str
    databank: str
    rows: list[Row]


class Discard(BaseModel):
    """Strategies the owner deleted by hand, by identity."""

    project: str
    databank: str
    identities: list[str]


class Bank(BaseModel):
    """One databank of one project."""

    project: str
    databank: str


class Saved(BaseModel):
    """A filter kept under a name."""

    name: str
    rows: list[Row]


def shown(what: str, act: Callable[[], dict]) -> dict:
    """One call for the window, a failure as `error` instead of a 500 (the ui boundary)."""
    try:
        return act()
    except Exception as failed:  # noqa: BLE001 — a report half-written, the door refusing
        return {"error": f"No se pudo {what}: {failed}"}


def context(project: str, databank: str) -> tuple[dict, dict, list[dict]]:
    """The databank's table, its distributions by identity and the metrics a filter may read."""
    table = tablemod.table(project, databank)
    row = where.enrolled(project)
    studies = evaluate.refused(row["symbol"] if row else None)
    by_id = dists.project(project, studies)
    return table, by_id, evaluate.offered(table, by_id, studies)


def anonymous(table: dict) -> int:
    """Rows only a report without identity names: shown, but no filter can hide them."""
    return sum(r["identity"] is None for r in table["rows"])


def worded(step: dict) -> str:
    """A step's expression for the funnel, each metric in the window's words (a step logged
    before the expression was worded still carries raw keys), and its «sin valor» and
    «sin identidad» counts."""
    parts = [re.match(r"^(.*?) (>|<|≥|≤|=|entre|dentro|fuera) (.*)$", p)
             for p in step["expression"].split(" AND ")]
    text = step["expression"] if step["origin"] == "manual" else " AND ".join(
        f"{evaluate.named(m.group(1))} {m.group(2)} {m.group(3)}" for m in parts)
    return (text + (f" · {step['blank']} sin valor" if step["blank"] else "")
            + (f" · {step['anonymous']} sin identidad, no filtrables" if step["anonymous"]
               else ""))


def samples(rows: list[dict], metrics: list[dict]) -> set[str]:
    """The samples a filter reads: `IS`, `OOS`, or '' for a study's column or a distribution."""
    known = {m["key"]: m["sample"] for m in metrics}
    return {known[r["metric"]] for r in rows}


def state_of(project: str, databank: str) -> dict:
    """One databank's discards now: hidden identities and each filter's counts."""
    steps = discards.steps(project, databank)
    hidden = discards.hidden(project, databank)
    return {"databank": databank, "hidden": len(hidden), "hidden_ids": sorted(hidden),
            "entered": steps[0]["entered"] if steps else None,
            "remaining": steps[-1]["passed"] if steps else None,
            "anonymous": steps[-1]["anonymous"] if steps else None, "steps": steps}


def funnel_rows(project: str, banks: list[str]) -> list[dict]:
    """The funnel's rows (screen, entered, passed, died, why), one per filter or deletion."""
    return [{"screen": f"Filtro · {bank}" if s["origin"] == "filter" else f"A mano · {bank}",
             "entered": s["entered"], "passed": s["passed"], "died": s["died"],
             "why": worded(s), "kind": "hard"}
            for bank in banks for s in discards.steps(project, bank)]


def refused(project: str, databank: str) -> str | None:
    """Why a filter on this databank cannot be logged, and so is not applied; None if it can."""
    who = ledgerrow.signed(project)
    if isinstance(who, str):
        return who
    where = ledgerrow.placed(project, databank)
    return where if isinstance(where, str) else None


def metrics_of(project: str, databank: str) -> dict:
    """What the metric dropdown lists, and why the databank cannot be filtered, if it cannot."""
    table, _, metrics = context(project, databank)
    return {"metrics": metrics, "refused": refused(project, databank),
            "anonymous": anonymous(table),
            "ops": list(evaluate.SHOWN), "intervals": sorted(dists.PAIRS)}


@ROUTER.get("/api/filters/metrics")
def get_metrics(project: str, databank: str) -> dict:
    """The metric dropdown's contents (`metrics_of`)."""
    return shown("leer las métricas", lambda: metrics_of(project, databank))


def applied(req: Apply) -> dict:
    """Apply an AND of rows to what is visible: one ledger row, then the discards on disk.

    Returns:
        `n_in`, `n_out`, `blank` (kept visible for lacking a value), `expression`, `ledger`
        (study, step, segment) and the databank's new state — or `error`, and nothing written.
        No `.sqx` is touched: SQX's databank stays whole until «Continuar workflow».
    """
    why = refused(req.project, req.databank)
    if why:
        return {"error": why}
    table, by_id, metrics = context(req.project, req.databank)
    rows = evaluate.normal([r.model_dump() for r in req.rows])
    bad = evaluate.check(rows, metrics)
    if bad:
        return {"error": bad}
    hidden = discards.hidden(req.project, req.databank)
    visible, dropped, blank = evaluate.judge(table, rows, by_id, hidden)
    text = evaluate.expression(rows)
    step, _ = ledgerrow.placed(req.project, req.databank)
    wrote = ledgerrow.log(req.project, req.databank, step, samples(rows, metrics),
                          len(visible), len(visible) - len(dropped), text, "filter", rows)
    discards.record(req.project, req.databank, dropped, "filter", text, len(visible), blank,
                    anonymous(table))
    return {"n_in": len(visible), "n_out": len(visible) - len(dropped), "blank": blank,
            "expression": text, "ledger": {k: wrote[k] for k in ("study", "step", "segment")},
            **state_of(req.project, req.databank)}


@ROUTER.post("/api/filters/apply")
def apply(req: Apply) -> dict:
    """«Aplicar» (`applied`)."""
    return shown("aplicar el filtro", lambda: applied(req))


def discarded(req: Discard) -> dict:
    """Delete strategies by hand: the same log and the same one ledger row as a filter."""
    why = refused(req.project, req.databank)
    if why:
        return {"error": why}
    table = tablemod.table(req.project, req.databank)
    hidden = discards.hidden(req.project, req.databank)
    visible = {r["identity"]: r["name"] for r in table["rows"]
               if r["identity"] and r["identity"] not in hidden}
    dropped = {i: visible[i] for i in req.identities if i in visible}
    if not dropped:
        return {"error": "ninguna de las seleccionadas está visible con identidad"}
    text = f"descarte manual de {len(dropped)}: {', '.join(sorted(dropped.values()))}"
    step, _ = ledgerrow.placed(req.project, req.databank)
    wrote = ledgerrow.log(req.project, req.databank, step, {"IS", "OOS", ""},
                          len(visible), len(visible) - len(dropped), text, "manual", None)
    discards.record(req.project, req.databank, dropped, "manual", text, len(visible), 0,
                    anonymous(table))
    return {"n_in": len(visible), "n_out": len(visible) - len(dropped), "expression": text,
            "ledger": {k: wrote[k] for k in ("study", "step", "segment")},
            **state_of(req.project, req.databank)}


@ROUTER.post("/api/filters/discard")
def discard(req: Discard) -> dict:
    """«Descartar seleccionadas» (`discarded`)."""
    return shown("descartar", lambda: discarded(req))


@ROUTER.post("/api/filters/clear")
def clear(req: Bank) -> dict:
    """«Quitar filtros»: every strategy visible again. The ledger keeps what was looked at."""
    return shown("quitar los filtros", lambda: {
        "back": discards.clear(req.project, req.databank),
        **state_of(req.project, req.databank)})


def state(project: str, databank: str | None) -> dict:
    """The funnel's counts: one databank's state, or every filtered databank's rows."""
    banks = [databank.replace(" ", "_")] if databank else discards.databanks(project)
    out = {"rows": funnel_rows(project, banks)}
    return out | state_of(project, databank) if databank else out


@ROUTER.get("/api/filters/state")
def get_state(project: str, databank: str | None = None) -> dict:
    """`state`, for the strip (with `databank`) and for the funnel (without)."""
    return shown("leer el estado de los filtros", lambda: state(project, databank))


@ROUTER.get("/api/filters/saved")
def get_saved() -> dict:
    """Every filter saved by name."""
    return shown("leer los filtros guardados", lambda: {"saved": saved.every()})


@ROUTER.post("/api/filters/saved")
def post_saved(req: Saved) -> dict:
    """Keep a filter under a name."""
    return shown("guardar el filtro", lambda: {
        "name": req.name, **saved.save(req.name, evaluate.normal([r.model_dump()
                                                                 for r in req.rows]))})
