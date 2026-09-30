"""The filter routes: metrics, preview, apply, manual discard, clear, state, saved filters."""

from collections.abc import Callable

from fastapi import APIRouter
from pydantic import BaseModel

from ui.daemon.databank import table as tablemod
from ui.daemon.filters import discards, dists, evaluate, ledgerrow, saved, view
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


def samples(rows: list[dict], metrics: list[dict]) -> set[str]:
    """The samples a filter reads: `IS`, `OOS`, or '' for a study's column or a distribution."""
    known = {m["key"]: m["sample"] for m in metrics}
    return {known[r["metric"]] for r in rows}


def state_of(project: str, databank: str, got: tuple | None = None) -> dict:
    """`view.state_of` over a `context` the caller already read, or read once here."""
    table, _, metrics = got or context(project, databank)
    return view.state_of(project, databank, table, metrics)


def refused(project: str, databank: str) -> str | None:
    """Why a filter on this databank cannot be logged, and so is not applied; None if it can."""
    who = ledgerrow.signed(project)
    if isinstance(who, str):
        return who
    where = ledgerrow.placed(project, databank)
    return where if isinstance(where, str) else None


def metrics_of(project: str, databank: str, got: tuple | None = None) -> dict:
    """What the metric dropdown lists, and why the databank cannot be filtered, if it cannot."""
    table, _, metrics = got or context(project, databank)
    return {"metrics": metrics, "refused": refused(project, databank),
            "anonymous": anonymous(table),
            "ops": list(evaluate.SHOWN), "intervals": sorted(dists.PAIRS)}


@ROUTER.get("/api/filters/metrics")
def get_metrics(project: str, databank: str) -> dict:
    """The metric dropdown's contents (`metrics_of`)."""
    return shown("leer las métricas", lambda: metrics_of(project, databank))


def judged(req: Apply) -> dict:
    """The AND of rows on the whole databank, manual deletions apart; nothing written.

    Returns:
        `rows` (normalised), `got` (the `context` read), `every` (identity → name),
        `dropped`, `blank`, `hidden` (dropped plus the manual deletions still in the table),
        or `error`.
    """
    table, by_id, metrics = context(req.project, req.databank)
    rows = evaluate.normal([r.model_dump() for r in req.rows])
    bad = evaluate.check(rows, metrics) if rows else None
    if bad:
        return {"error": bad}
    every, dropped, blank = evaluate.judge(table, rows, by_id, set())
    manual = discards.manual_ids(req.project, req.databank) & set(every)
    return {"rows": rows, "got": (table, by_id, metrics), "every": every, "dropped": dropped,
            "blank": blank, "hidden": len(set(dropped) | manual)}


@ROUTER.post("/api/filters/preview")
def preview(req: Apply) -> dict:
    """What these conditions would leave, as the owner edits them: counts only, no ledger
    row, no discard, nothing hidden (the screen keeps showing what «Continuar» would cut)."""
    def act() -> dict:
        """The counts of `judged`, or its error."""
        got = judged(req)
        return got if "error" in got else {
            "n_in": len(got["every"]), "n_out": len(got["every"]) - len(got["dropped"]),
            "blank": got["blank"], "hidden": got["hidden"],
            "visible": len(got["every"]) - got["hidden"]}
    return shown("calcular el filtro", act)


def applied(req: Apply) -> dict:
    """Apply an AND of rows to the whole databank, replacing the filter in force: loosening
    brings strategies back, tightening hides more; manual deletions stay. One ledger row
    (none for no conditions, which only lifts the filter), then the discards on disk.

    Returns:
        `n_in`, `n_out`, `blank` (kept visible for lacking a value), `expression`, `ledger`
        (study, step, segment; absent without conditions) and the databank's new state —
        or `error`, and nothing written; `same` when these rows are already in force.
        No `.sqx` is touched: SQX's databank stays whole until «Continuar workflow».
    """
    why = refused(req.project, req.databank)
    if why:
        return {"error": why}
    got = judged(req)
    if "error" in got:
        return got
    rows, n_in = got["rows"], len(got["every"])
    n_out = n_in - len(got["dropped"])
    counts = {"n_in": n_in, "n_out": n_out, "blank": got["blank"]}
    if discards.unchanged(req.project, req.databank, rows, n_in, set(got["dropped"])):
        return {**counts, "same": True, **state_of(req.project, req.databank, got["got"])}
    text, led = (evaluate.expression(rows) if rows else "sin filtro"), {}
    if rows:
        step, _ = ledgerrow.placed(req.project, req.databank)
        wrote = ledgerrow.log(req.project, req.databank, step,
                              samples(rows, got["got"][2]), n_in, n_out, text, "filter", rows)
        led = {"ledger": {k: wrote[k] for k in ("study", "step", "segment")}}
    discards.record(req.project, req.databank, got["dropped"], "filter", text, n_in,
                    got["blank"], anonymous(got["got"][0]), rows)
    return {**counts, "expression": text, **led,
            **state_of(req.project, req.databank, got["got"])}


@ROUTER.post("/api/filters/apply")
def apply(req: Apply) -> dict:
    """«Aplicar» (`applied`)."""
    return shown("aplicar el filtro", lambda: applied(req))


def discarded(req: Discard) -> dict:
    """Delete strategies by hand: the same log and the same one ledger row as a filter."""
    why = refused(req.project, req.databank)
    if why:
        return {"error": why}
    got = context(req.project, req.databank)
    table, hidden = got[0], discards.hidden(req.project, req.databank)
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
                    anonymous(table), total=len(table["rows"]) - anonymous(table))
    return {"n_in": len(visible), "n_out": len(visible) - len(dropped), "expression": text,
            "ledger": {k: wrote[k] for k in ("study", "step", "segment")},
            **state_of(req.project, req.databank, got)}


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
    """The funnel's counts: every filtered databank's rows, and with a databank its state
    and its metrics too, read off one `context` (the strip's one call per table refresh)."""
    banks = [databank.replace(" ", "_")] if databank else discards.databanks(project)
    out = {"rows": view.funnel_rows(project, banks)}
    if not databank:
        return out
    got = context(project, databank)
    return out | metrics_of(project, databank, got) | state_of(project, databank, got)


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
