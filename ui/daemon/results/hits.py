"""Every stored result that could answer for one strategy across the whole project, found cheaply: file
stats and cached slim reads, never a full parse per question."""

import re
from collections.abc import Iterator
from pathlib import Path

from ui.daemon.databank.batches import STUDIES as BATCH_STUDIES
from ui.daemon.databank.batches import batches
from ui.daemon.databank.cells import norm
from ui.daemon.results import lote, store
from ui.daemon.results.slice import KEYS, mine

NOT_CONTRACT = "informe anterior al contrato de estudios (sin tabs ni config_hash)"


def aliases(name: str) -> list[str]:
    """Every spelling a writer gives one strategy's name: `Strategy 1.26.46` and `1.26.46`
    (the MC Retest ingest drops the prefix, 📓 2026-09-30), the one asked for first."""
    base = re.sub(r"^Strategy[ _]", "", name)
    return list(dict.fromkeys([name, f"Strategy {base}", base]))


def _named(path: Path) -> frozenset[str]:
    """Every strategy name a population result's blocks speak of, as `slice.block` reads them."""
    got, _ = store.load(path)
    found = set()
    for tab in (got or {}).get("tabs", []):
        for b in tab.get("blocks", []):
            at = [i for i, c in enumerate(b.get("columns") or []) if c in KEYS]
            found |= {str(r[i]) for r in b.get("rows") or [] for i in at
                      if b.get("kind") == "table"}
            found |= {str(i.get("label", "")).split(" · ")[0] for i in b.get("items") or []}
            found |= {str(r) for r in b.get("rows") or [] if b.get("kind") == "grid"}
    return frozenset(found)


def named(path: Path, names: list[str]) -> str | None:
    """The spelling under which a population result names this strategy, or None.

    Args:
        path: A population `<study>.json`.
        names: `aliases` of the strategy.

    Returns:
        The first alias some block names (itself or a `_Scaled` sibling); parsed once per
        version of the file.
    """
    said = store.cached(path, _named)
    return next((a for a in names if any(mine(s, a) for s in said)), None)


def layout(project: str) -> dict[str, dict[str, list[str]]]:
    """Every databank of the project, and per study the days it holds, newest first.

    Returns:
        Folder name → study → days. One `iterdir` per day folder, a few dozen in all.
    """
    root = store.bank(project, "x").parent
    out: dict[str, dict[str, list[str]]] = {}
    for db in sorted(root.iterdir()) if root.is_dir() else []:
        if not db.is_dir() or db.name.startswith("_"):
            continue
        studies = out.setdefault(db.name, {})
        for day in sorted((d for d in db.iterdir() if d.is_dir()), reverse=True):
            for s in day.iterdir():
                if s.is_dir():
                    studies.setdefault(s.name, []).append(day.name)
    return out


def _hit(path: Path, kind: str, row: dict, **more: object) -> dict:
    """One candidate: where it is, what it said, and what its identity is."""
    return {"path": path, "kind": kind, "config_hash": row["config_hash"],
            "computed_at": row["computed_at"], "state": row["state"], "label": row["label"],
            "manifest": None, "note": "", "population": False, **more}


def in_folder(folder: Path, study: str, strategy: str, day: str) -> dict:
    """What one study folder of one day holds for the population or one strategy.

    Args:
        folder: reports/<P>/<D>/<day>/<study>/.
        study: Study key.
        strategy: Strategy name, "" for the population.
        day: The folder's day.

    Returns:
        A hit (`kind` file, slice, row, whole or population), or `{"skip": reason}`.
    """
    base = {"day": day, "manifest": folder / "manifest.json"}
    population = folder / f"{study}.json"
    if strategy:
        names = aliases(strategy)
        table = store.verdicts(folder) or {}
        for a in names:
            path = folder / "estrategias" / f"{a}.json"
            if path.is_file():
                row = store.slim(path)
                if row is None:
                    return {"skip": NOT_CONTRACT}
                return _hit(path, "file", row, alias=a, **base,
                            identity=row["identity"] or table.get(a, {}).get("identity"))
    whole = store.slim(population) if population.is_file() else None
    if whole is None:
        return {"skip": NOT_CONTRACT if population.is_file() else "no hay resultado guardado"}
    if not strategy:
        return _hit(population, "population", whole, alias="", identity=None, population=True,
                    **base)
    at = named(population, names)
    row_at = next((a for a in names if a in table), None)
    alone = not (folder / "estrategias").is_dir()
    kind = "slice" if at else "row" if row_at else "whole" if alone else None
    if kind is None:
        return {"skip": "el run de la población no nombra esta estrategia"}
    alias = at or row_at or strategy
    row = table.get(alias)
    said = ({**whole, "state": store.WORDS.get(row["word"], "none"), "label": row["word"]}
            if row else whole)
    return _hit(population, kind, said, alias=alias, population=True, **base,
                identity=row["identity"] if row else None)


def _batch(project: str, study: str, strategy: str) -> Iterator[dict]:
    """A batch study's one result for a mother (`cloud`/`wfc`/`cscv`/`marketSurfaces`)."""
    found = batches(project).get(norm(strategy), [])
    if len(found) != 1:
        yield {"skip": "dos lotes de variantes para esta madre: sin uno solo que leer" if found
               else "esta estrategia no es madre de ningún lote de variantes", "day": ""}
        return
    path = found[0] / "estudios" / f"{study}.json"
    row = store.slim(path) if path.is_file() else None
    if row is None:
        yield {"skip": NOT_CONTRACT if path.is_file() else "no hay resultado guardado", "day": ""}
        return
    # Its `estudios/manifest.json` is shared by every study of the batch: not this run's.
    yield _hit(path, "file", row, alias=strategy, day=(row["computed_at"] or "")[:10],
               identity=row["identity"], origin=f"lote {found[0].name}", elsewhere=None)


def _lote(project: str, study: str, strategy: str) -> Iterator[dict]:
    """A one-off multi-mother lote's results for this strategy, newest first (the ATR pass1 and
    pass2 both answer: the owner reads the newest, told which pass it is — 2026-10-01)."""
    found = [(p, row) for a in aliases(strategy) for p in lote.paths(project, study, a)
             for row in [store.slim(p)] if row is not None]
    found.sort(key=lambda f: f[1]["computed_at"] or "", reverse=True)
    for i, (path, row) in enumerate(found):
        name = lote.name(path)
        note = f"lote {name}" + (f", el más nuevo de {len(found)}" if i == 0 and len(found) > 1
                                 else "")
        yield _hit(path, "file", row, alias=strategy, day=(row["computed_at"] or "")[:10],
                   identity=row["identity"], origin=f"lote {name}", elsewhere=None, note=note,
                   manifest=path.parent.parent / "manifest.json")


def sources(project: str, databank: str, study: str, strategy: str,
            day: str = "") -> Iterator[dict]:
    """Every candidate result, in the order they are preferred when identity does not decide.

    This databank's days newest first; then, for a strategy, the one-off lotes and every other
    databank of the project, newest report first — a strategy is one entity across the
    project (owner, 2026-09-30). A batch study reads only the mother's variant batch.

    Args:
        project: SQX project name.
        databank: The databank the page opened from, either spelling.
        study: Study key.
        strategy: Strategy name, "" for the population (this databank only).
        day: Keep only results of this day, "" for all.

    Yields:
        Hits (`origin`, `elsewhere`, `day`, `path`, `kind`, `alias`, `identity`,
        `config_hash`, `computed_at`, `state`, `label`, `population`, `manifest`, `note`) and
        `{"skip", "day"}` for a folder passed over with its reason.
    """
    if study in BATCH_STUDIES:
        yield from (_batch(project, study, strategy) if strategy else
                    iter([{"skip": "este estudio solo tiene resultado por madre, en su lote "
                                   "de variantes", "day": ""}]))
        return
    here = databank.replace(" ", "_")
    tree = layout(project)
    others = sorted((d for d in tree if d != here), key=lambda d: max(
        (x for days in tree[d].values() for x in days), default=""), reverse=True)
    for db in [here, None, *others] if strategy else [here]:
        if db is None:                       # the lotes, project-wide, before other databanks
            found = _lote(project, study, strategy) if study in lote.ROOTS else iter([])
            yield from (h for h in found if not day or h["day"] == day)
            continue
        for d in tree.get(db, {}).get(study, []):
            if day and d != day:
                continue
            got = in_folder(store.bank(project, db) / d / study, study, strategy, d)
            yield {**got, "day": d, "origin": db, "elsewhere": None if db == here else db}
