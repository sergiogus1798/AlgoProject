"""The population matrix: every strategy of one databank against every study, one state per cell."""

from collections import Counter
from pathlib import Path

from ui.daemon.results import catalogue, stale, store
from ui.daemon.loader import find


def _column(folder: Path, project: str) -> tuple[dict, list[dict]]:
    """One study folder's cells, keyed by identity.

    Args:
        folder: reports/<P>/<D>/<day>/<study>/.
        project: SQX project name, whose runner substitutions `stale.fresh` signs with.

    Returns:
        (identity -> {strategy, state, label, stale}, skipped). Each strategy's own JSON
        wins; verdict.csv fills the strategies it did not write, its word mapped by
        `store.WORDS` and its staleness read from the population result of the same run.
        A strategy with no identity anywhere cannot be paired and is skipped, counted; a
        folder that yields no cell at all says why with a count of 0.
    """
    table = store.verdicts(folder) or {}
    manifest = folder / "manifest.json"
    one, many = (stale.fresh(folder.name, project, manifest, p) for p in (False, True))
    cells, skipped, seen = {}, Counter(), set()
    for path in folder.glob("estrategias/*.json"):
        row = store.slim(path)
        if row is None:
            skipped["informe anterior al contrato de estudios"] += 1
            continue
        seen.add(row["strategy"])
        identity = row["identity"] or table.get(row["strategy"], {}).get("identity")
        if not identity:
            skipped["sin identidad"] += 1
            continue
        cells[identity] = {"strategy": row["strategy"], "state": row["state"],
                           "label": row["label"],
                           "stale": bool(one) and row["config_hash"] not in one}
    population = folder / f"{folder.name}.json"
    whole = store.slim(population) if population.is_file() else None
    signed = whole["config_hash"] if whole else None
    for name, row in table.items():
        if name in seen:
            continue
        if not row["identity"]:
            skipped["sin identidad"] += 1
            continue
        cells[row["identity"]] = {
            "strategy": name, "state": store.WORDS.get(row["word"], "none"), "label": row["word"],
            "stale": None if signed is None or not many else signed not in many}
    if not cells and not skipped:
        skipped["ni JSON por estrategia del contrato ni verdict.csv con estrategia y veredicto"] = 0
    rel = f"{folder.parent.name}/{folder.name}"
    return cells, [{"path": rel, "reason": why, "n": n} for why, n in skipped.items()]


def matrix(project: str, databank: str) -> dict:
    """Every strategy any study judged in one databank, and what each study said of it.

    Args:
        project: SQX project name.
        databank: Databank name.

    Returns:
        `studies` (every catalogue key, family order), `present` (those with a cell here),
        `strategies` [{strategy, identity}] by name, `cells` identity -> study ->
        {state, label, stale, day} from the newest day that judged that identity, and
        `skipped` — folders that are not a study and strategies that could not be paired,
        each with its reason. Pairing is by identity: two days can use one name for two
        different strategies. Only this databank's reports are read, because a retest
        databank signs its strategies with other identities than the build's.
    """
    root = store.bank(project, databank)
    cells: dict[str, dict] = {}
    names: dict[str, str] = {}
    skipped = []
    for day in sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []:
        for folder in sorted(p for p in day.iterdir() if p.is_dir()):
            if folder.name not in catalogue.STUDIES:
                skipped.append({"path": f"{day.name}/{folder.name}", "n": None,
                                "reason": "no es un estudio del catálogo"})
                continue
            got, lost = _column(folder, project)
            skipped += lost
            for identity, cell in got.items():
                names[identity] = cell.pop("strategy")
                cells.setdefault(identity, {})[folder.name] = cell | {"day": day.name}
    # The databank's own files, so a strategy no study has judged yet is still a row.
    for identity, name in find.roster(project, databank).items():
        names.setdefault(identity, name)
    present = {s for row in cells.values() for s in row}
    order = catalogue.ordered()
    return {"studies": order, "present": [k for k in order if k in present],
            "strategies": sorted(({"strategy": n, "identity": i} for i, n in names.items()),
                                 key=lambda r: r["strategy"]),
            "cells": cells, "skipped": skipped}
