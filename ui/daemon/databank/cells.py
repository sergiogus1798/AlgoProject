"""What every study said of each strategy of a project, per databank: verdict, state and fields."""

import re
from pathlib import Path

from core.paths import DATA
from ui.daemon.results import catalogue, store

# Columns of a verdict.csv that are not a field of the strategy: its keys and the word itself.
KEYS = {"strategy", "identity", "verdict", "verdict_state", "mother"}

# A verdict.csv with one row per strategy and per something else: that column becomes the
# sub-panel (crossTF writes one row per mother and timeframe).
SPLIT = {"crossTF": "timeframe"}

# A per-strategy table whose rows become sub-panels: its title, first column the sub's name
# (the eight MC Retest tasks, the markets of the cross-market paired test).
SUBTABLE = {"mcRetest": "Qué hizo cada tarea", "crossmarket": "Pareado (1b)"}

# How bad a state is, to give a strategy split in several rows one state of its own.
SEVERITY = ("fail", "watch", "pass", "info", "none")


def norm(name: str) -> str:
    """A strategy name as every writer spells it: `Strategy 9.27.83`, `9.27.83`,
    `Strategy_9.27.83` and the pipeline's `Strategy_9-27-83` all give `9.27.83`."""
    return re.sub(r"^Strategy[ _]", "", name).replace("-", ".")


def scalar(text: str) -> object:
    """A CSV cell as a number when it is one, else its text; empty is None."""
    if text in ("", None):
        return None
    try:
        return float(text)
    except ValueError:
        return text


def worst(states: list[str]) -> str:
    """The most severe of several states."""
    return min(states, key=lambda s: SEVERITY.index(s) if s in SEVERITY else len(SEVERITY))


def from_csv(study: str, folder: Path) -> dict[str, dict]:
    """A study folder's verdict.csv as one entry per strategy name.

    Args:
        study: Catalogue key.
        folder: reports/<P>/<D>/<day>/<study>/.

    Returns:
        name → {identity, verdict, state, fields {(sub, field): value}}. A split study's
        rows fold into one entry, its words under their sub and its own state the worst.
    """
    out: dict[str, dict] = {}
    for row in store.rows(folder):
        name = row["strategy"]
        word = row.get("verdict") or None
        state = row.get("verdict_state") or store.WORDS.get(word, "none")
        entry = out.setdefault(name, {"identity": row.get("identity") or None, "verdict": None,
                                      "state": state, "states": {}, "fields": {}})
        sub = row.get(SPLIT[study]) if study in SPLIT else ""
        for key, text in row.items():
            if key not in KEYS and key != SPLIT.get(study):
                entry["fields"][(sub, key)] = scalar(text)
        if sub:
            entry["fields"][(sub, "verdict")] = word
            entry["states"][sub] = state
            entry["state"] = worst(list(entry["states"].values()))
        else:
            entry["verdict"] = word
    return out


def from_json(study: str, folder: Path, found: dict[str, dict]) -> None:
    """Lay each per-strategy result over the CSV's entries: its verdict wins, and a study with
    a per-task or per-market table adds one sub-panel per row of it.

    Args:
        study: Catalogue key.
        folder: The study folder.
        found: What `from_csv` returned, completed in place.
    """
    for path in folder.glob("estrategias/*.json"):
        row = store.slim(path)
        if row is None:
            continue
        entry = found.setdefault(row["strategy"], {"identity": None, "verdict": None,
                                                   "state": "none", "states": {}, "fields": {}})
        entry["identity"] = row["identity"] or entry["identity"]
        entry["verdict"], entry["state"] = row["label"], row["state"]
        table = (store.tables(path) or {}).get(SUBTABLE.get(study))
        for line in table["rows"] if table else []:
            for column, value in zip(table["columns"][1:], line[1:]):
                entry["fields"][(str(line[0]), column)] = value


def folder_cells(study: str, folder: Path) -> dict[str, dict]:
    """One study folder, one entry per strategy name, with the day it was judged."""
    found = from_csv(study, folder)
    from_json(study, folder, found)
    return {name: {**e, "name": name, "day": folder.parent.name} for name, e in found.items()}


def project(project_name: str) -> dict[str, dict]:
    """Every databank's study entries of one project, the newest day of each study winning.

    Args:
        project_name: Project name.

    Returns:
        databank folder → {"by_id": {identity: {study: entry}}, "by_name": {norm name:
        {study: entry}}}. Only catalogue studies under `reports/<P>/<D>/<day>/` are read;
        the variant batch's studies come from `batches.py`.
    """
    out: dict[str, dict] = {}
    for bank in sorted(p for p in (DATA / "reports" / project_name).glob("*") if p.is_dir()):
        mine = out.setdefault(bank.name, {"by_id": {}, "by_name": {}})
        for folder in sorted(bank.glob("*/*")):
            if folder.name not in catalogue.STUDIES or not folder.is_dir():
                continue
            for name, entry in folder_cells(folder.name, folder).items():
                mine["by_name"].setdefault(norm(name), {})[folder.name] = entry
                if entry["identity"]:
                    mine["by_id"].setdefault(entry["identity"], {})[folder.name] = entry
    return out


def anywhere(every: dict[str, dict]) -> dict[str, dict]:
    """Every databank's entries by identity, the newest day winning across databanks.

    Args:
        every: What `project` returned.

    Returns:
        identity → {study: entry}. An identity is the strategy's own content hash, so a
        retest databank that kept it (mcRetest, crossTF sign the build's) pairs exactly.
    """
    out: dict[str, dict] = {}
    for bank in every.values():
        for identity, studies in bank["by_id"].items():
            mine = out.setdefault(identity, {})
            for study, entry in studies.items():
                if study not in mine or entry["day"] > mine[study]["day"]:
                    mine[study] = entry
    return out
