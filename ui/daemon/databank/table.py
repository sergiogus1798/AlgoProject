"""One databank as SQX shows it: a row per strategy, its metrics, and a column group per study."""

import math
import threading
from concurrent.futures import Future
from typing import Any, TypedDict, cast

import pandas as pd

from ui.daemon.databank import batches, cells, metrics
from ui.daemon.loader import find
from ui.daemon.results import catalogue, store
from ui.daemon.workflow import ledgerview
from ui.daemon.workflow.records import Door

# Read together or not at all (WORKFLOW.md «los tres a la vez»), and step 20 after them: while
# the ledger's door is shut none of their figures leaves the daemon.
SEALED = ("wfc", "cscv", "wfm", "blindJoint")

# A study field the databank table never shows as a column, though the study keeps it (other
# tables, the ficha's own view, read the entry directly): the owner's Cross Market databank
# read (2026-09-30) — «Nota» clutters the table without deciding anything there.
HIDDEN_FIELDS = {("crossmarket", "note"),
                 ("mcRetest", "qué perturba"), ("mcRetest", "operaciones vs original"),
                 ("mcRetest", "forma"), ("blindJoint", "reason")}
# 🔬 2026-10-04: opening a project asks for the same 10,000-row table three times at once
# (the tab list, the table, the filters), and the three builds shared one GIL: 60 s against
# the window's 20. Whoever asks while a build is in flight waits for it and reads its answer.
FLIGHTS: dict[tuple[str, str], "Future[Table]"] = {}
GUARD = threading.Lock()


class _Col(TypedDict):
    """The two keys every table column carries."""

    key: str
    kind: str


class Column(_Col, total=False):
    """One table column: `key` and `kind` always, the rest by kind (metric or study)."""

    metric: str
    sample: str
    study: str
    sub: str
    field: str
    title: str


class Row(TypedDict):
    """One strategy's row: `identity` None for a name-only row, `values` one per column."""

    identity: str | None
    name: str
    values: list[object]
    states: dict[str, str]


class Table(TypedDict):
    """The `build` payload; `held_by` and `sealed` are None when they do not apply."""

    databank: str
    rows_from: str
    held_by: str | None
    writing: bool
    metrics_from: str
    columns: list[Column]
    rows: list[Row]
    studies: list[str]
    sealed: dict[str, Any] | None


def door(project: str) -> tuple[Door, str | None]:
    """The ledger's door of step 20 — the very one the rail asks — and the project's asset.

    Returns:
        (`ledgerview.door` — `sealed`, `done`, `text`, `study` —, the asset or None).
    """
    rows = ledgerview.frame(ledgerview.studies_of(project))
    return ledgerview.door(project), ledgerview.symbol(rows, project)


def roster(project: str, databank: str, own: dict,
           figures: pd.DataFrame | None) -> tuple[str, dict[str, str]]:
    """The rows: the databank's files, or — when no install holds it any more — what the
    cosecha and this databank's reports remember of it.

    Returns:
        (`archivos` or `informes`, key → name). A key is the identity, or `name:<name>` for
        a strategy only a report without identity names.
    """
    held = find.roster(project, databank)
    if held:
        return "archivos", held
    by_id = figures is not None and "name" in figures
    rows = dict(zip(figures.index, figures["name"])) if figures is not None and by_id else {}
    for identity, studies in own["by_id"].items():
        rows.setdefault(identity, next(iter(studies.values()))["name"])
    named = {cells.norm(n) for n in rows.values()}
    for name, studies in own["by_name"].items():
        if name not in named and not any(e["identity"] for e in studies.values()):
            rows[f"name:{name}"] = next(iter(studies.values()))["name"]
            named.add(name)
    for name in figures.index if figures is not None and not by_id else []:
        if cells.norm(name) not in named:
            rows[f"name:{cells.norm(name)}"] = name
    if databank.replace(" ", "_") == "MCR_All":
        # The MC ingest names «1.26.46»: the page would open a name no other study knows
        # (📓 2026-09-30); `results.api` strips the prefix again when it asks mcRetest.
        rows = {k: n if n.startswith("Strategy ") else f"Strategy {n}" for k, n in rows.items()}
    return "informes", rows


def studies_of(key: str, name: str, own: dict, every: dict, mothers: dict) -> dict[str, dict]:
    """What each study said of one row: this databank's reports by identity, then by name,
    then any databank of the project by identity, then the mother's variant batch by name."""
    found = dict(mothers.get(cells.norm(name), {}))
    found |= every.get(key, {})
    found |= own["by_name"].get(cells.norm(name), {})
    found |= own["by_id"].get(key, {})
    return found


def clean(value: Any) -> object:
    """A value JSON can carry: numpy scalars as Python ones, NaN as None."""
    value = value.item() if hasattr(value, "item") else value
    return None if isinstance(value, float) and math.isnan(value) else value


def figures_by_row(figures: pd.DataFrame | None) -> dict[Any, dict[str, Any]]:
    """A metrics frame as index → {column: value}: 10,000 rows of 34 figures read one
    `.loc` and one `.get` at a time cost 2 s of the table's 4 (🔬 2026-10-04). Transposed,
    so a row keeps the one dtype `.loc` gave it: an integer among floats is a float."""
    return {} if figures is None else figures.T.to_dict()


def table(project: str, databank: str) -> Table:
    """`build`, once for everybody who asks while it runs; nobody may change what it returns."""
    key = (project, find.spelled(project, databank))
    with GUARD:
        flight = FLIGHTS.get(key)
        mine = flight is None
        if mine:
            flight = FLIGHTS[key] = Future()
    if mine:
        try:
            flight.set_result(build(project, databank))
            store.keep()
        except Exception as failed:  # noqa: BLE001 — handed to every waiter, raised below
            flight.set_exception(failed)
        finally:
            with GUARD:
                del FLIGHTS[key]
    return flight.result()


def build(project: str, databank: str) -> Table:
    """GET /api/databank/table: the whole databank, every column the window may show.

    Args:
        project: Project name.
        databank: Either spelling.

    Returns:
        `databank`, `rows_from` (archivos | informes), `held_by` (the role whose folder
        is empty, None when no install has it), `writing` (SQX is writing that folder now:
        its files are not read, which is why the rows come from the reports), `metrics_from` (cosecha | export |
        ''), `columns` [{key, kind (name | metric | study), metric, sample, study, sub,
        field, title}], `rows` [{identity (None for a name-only row), name, values (one per
        column), states {verdict column key: state}}], `studies` present, and `sealed`
        {studies, text} when the ledger's door holds 17-19 and 20 back.
    """
    db = find.spelled(project, databank)
    every = cells.project(project)
    own = every.get(db.replace(" ", "_"), {"by_id": {}, "by_name": {}})
    anywhere, mothers = cells.anywhere(every), batches.mothers(project)
    got_from, figures = metrics.source(project, db)
    rows_from, keys = roster(project, db, own, figures)
    blind, _ = door(project)
    hidden = set(SEALED) if blind["sealed"] else set()
    lines, fields = [], {}
    for key, name in sorted(keys.items(), key=lambda kv: kv[1]):
        said = {s: e for s, e in studies_of(key, name, own, anywhere, mothers).items()
                if s not in hidden}
        for study, e in said.items():
            fields.setdefault((study, "", "verdict"), None)
            for sub, field in e["fields"]:
                if (study, field) in HIDDEN_FIELDS:
                    continue
                fields.setdefault((study, sub, field), None)
        lines.append((key, name, said))
    order = catalogue.ordered()
    rank = {}                                   # a study's subs in the order its data gives
    for study, sub, _ in fields:
        rank.setdefault((study, sub), -1 if not sub else len(rank))
    study_cols = sorted(fields, key=lambda f: (order.index(f[0]), rank[f[:2]], f[2] != "verdict"))
    figure_cols = [c for c in (figures.columns if figures is not None else []) if c != "name"]
    # A sample this databank never carries (Cross Market's OOS: no retest window) is empty in
    # every row, not just some — SQX's own «Export Data View» always offers the column, so the
    # daemon is the only place that can tell «never filled» from «this strategy made no trade»
    # (`metrics.empty_samples` blanks the latter per row). Drop only the former.
    if figures is not None:
        figure_cols = [c for c in figure_cols if not bool(figures[c].isna().all())]
    name_col: list[Column] = [{"key": "name", "kind": "name"}]
    metric_cols: list[Column] = [{"key": c, "kind": "metric", "metric": c.rsplit(" (", 1)[0],
                                  "sample": c.rsplit(" (", 1)[-1].rstrip(")") if " (" in c else ""}
                                 for c in figure_cols]
    study_defs: list[Column] = [{"key": ".".join(p for p in f if p), "kind": "study", "study": f[0],
                                 "sub": f[1], "field": f[2], "title": catalogue.STUDIES[f[0]][2]}
                                for f in study_cols]
    columns = name_col + metric_cols + study_defs
    by_id = got_from == "cosecha"
    # The cosecha holds only the strategies that had an OOS retest (H1: 60 of the build's 300);
    # the rest kept dashes in every metric though SQX's own export carries their figures
    # (owner's §4.1, 🔬 2026-10-01). A row the cosecha lacks reads the export, by name.
    spare = metrics.export(project, db) if by_id else None
    if spare is not None:
        spare = cast(pd.DataFrame, spare[~spare.index.map(cells.norm).duplicated()])
        spare.index = spare.index.map(cells.norm)
    rows, held, spared = [], figures_by_row(figures), figures_by_row(spare)
    for key, name, said in lines:
        figs = held.get(key if by_id else name) or spared.get(cells.norm(name))
        values = [name] + [clean(figs.get(c)) if figs is not None else None
                           for c in figure_cols]
        states = {}
        for study, sub, field in study_cols:
            e = said.get(study)
            if e is None:
                values.append(None)
                continue
            values.append(clean(e["verdict"] if (sub, field) == ("", "verdict")
                                else e["fields"].get((sub, field))))
            if field == "verdict":
                states[".".join(p for p in (study, sub, field) if p)] = (
                    e["states"].get(sub, e["state"]) if sub else e["state"])
        rows.append({"identity": None if key.startswith("name:") else key, "name": name,
                     "values": values, "states": states})
    where = find.install_of(project, db) if rows_from == "informes" else None
    return {"databank": db, "rows_from": rows_from, "held_by": where[0] if where else None,
            "writing": bool(where) and find.writing(where[1], project),
            "metrics_from": got_from,
            "columns": columns, "rows": rows,
            "studies": [s for s in order if any(f[0] == s for f in study_cols)],
            "sealed": {"studies": list(SEALED), "text": blind["text"]} if hidden else None}
