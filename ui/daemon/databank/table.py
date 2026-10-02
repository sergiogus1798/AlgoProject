"""One databank as SQX shows it: a row per strategy, its metrics, and a column group per study."""

import math

import pandas as pd

from ui.daemon.databank import batches, cells, metrics
from ui.daemon.loader import find
from ui.daemon.results import catalogue
from ui.daemon.workflow import ledgerview

# Read together or not at all (WORKFLOW.md «los tres a la vez»), and step 20 after them: while
# the ledger's door is shut none of their figures leaves the daemon.
SEALED = ("wfc", "cscv", "wfm", "blindJoint")

# A study field the databank table never shows as a column, though the study keeps it (other
# tables, the ficha's own view, read the entry directly): the owner's Cross Market databank
# read (2026-09-30) — «Familia», «Faltan», «Avisos», «Nota» clutter the table without deciding
# anything there.
HIDDEN_FIELDS = {("crossmarket", "family"), ("crossmarket", "missing"),
                 ("crossmarket", "warnings"), ("crossmarket", "note"),
                 ("mcRetest", "qué perturba"), ("mcRetest", "operaciones vs original"),
                 ("mcRetest", "forma"), ("blindJoint", "reason")}


def door(project: str) -> tuple[dict, str | None]:
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
    rows = dict(zip(figures.index, figures["name"])) if by_id else {}
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


def studies_of(key: str, name: str, own: dict, every: dict, mothers: dict, lotes: dict) -> dict:
    """What each study said of one row: this databank's reports by identity, then by name,
    then any databank of the project by identity, then the mother's variant batch by name,
    then the mother's one-off multi-mother lote (`structure`, `atrCalculator`) by name."""
    found = dict(lotes.get(cells.norm(name), {}))
    found |= dict(mothers.get(cells.norm(name), {}))
    found |= every.get(key, {})
    found |= own["by_name"].get(cells.norm(name), {})
    found |= own["by_id"].get(key, {})
    return found


def clean(value: object) -> object:
    """A value JSON can carry: numpy scalars as Python ones, NaN as None."""
    value = value.item() if hasattr(value, "item") else value
    return None if isinstance(value, float) and math.isnan(value) else value


def table(project: str, databank: str) -> dict:
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
    lotes = cells.lotes(project)
    got_from, figures = metrics.source(project, db)
    rows_from, keys = roster(project, db, own, figures)
    blind, _ = door(project)
    hidden = set(SEALED) if blind["sealed"] else set()
    lines, fields = [], {}
    for key, name in sorted(keys.items(), key=lambda kv: kv[1]):
        said = {s: e for s, e in studies_of(key, name, own, anywhere, mothers, lotes).items()
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
        figure_cols = [c for c in figure_cols if not figures[c].isna().all()]
    columns = ([{"key": "name", "kind": "name"}]
               + [{"key": c, "kind": "metric", "metric": c.rsplit(" (", 1)[0],
                   "sample": c.rsplit(" (", 1)[-1].rstrip(")") if " (" in c else ""}
                  for c in figure_cols]
               + [{"key": ".".join(p for p in f if p), "kind": "study", "study": f[0],
                   "sub": f[1], "field": f[2], "title": catalogue.STUDIES[f[0]][2]}
                  for f in study_cols])
    by_id = got_from == "cosecha"
    # The cosecha holds only the strategies that had an OOS retest (H1: 60 of the build's 300);
    # the rest kept dashes in every metric though SQX's own export carries their figures
    # (owner's §4.1, 🔬 2026-10-01). A row the cosecha lacks reads the export, by name.
    spare = metrics.export(project, db) if by_id else None
    if spare is not None:
        spare = spare[~spare.index.map(cells.norm).duplicated()]
        spare.index = spare.index.map(cells.norm)
    rows = []
    for key, name, said in lines:
        at = key if by_id else name
        figs = figures.loc[at] if figures is not None and at in figures.index else None
        if figs is None and spare is not None and cells.norm(name) in spare.index:
            figs = spare.loc[cells.norm(name)]
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
