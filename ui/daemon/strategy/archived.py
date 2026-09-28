"""The `source=archive` side of every Ficha route: an archived version read back, nothing computed."""

from pathlib import Path

import pandas as pd

from core.archive import read
from ui.daemon.results import catalogue
from ui.daemon.tearsheet.harvest import TRADES

SOURCES = ("live", "archive")


def bad_source(source: str) -> dict | None:
    """The refusal for a `source` other than live or archive, or None."""
    return None if source in SOURCES else {"error": f"Fuente «{source}» no válida: live o archive."}


def load(identity: str, version: str = "") -> dict | str:
    """One archived version, or the sentence of why there is none.

    Args:
        identity: The strategy's identity.
        version: A version folder name; "" for the newest.

    Returns:
        What `core.archive.read.load` returns, or the Spanish refusal.
    """
    try:
        return read.load(identity, version or None)
    except FileNotFoundError as missing:
        return str(missing)


def tearsheet(identity: str, version: str = "") -> dict | str:
    """The frozen cosecha rows the Ficha is built from, as `harvest.read` serves a live one.

    Versions archived before the Ficha read `Size` froze their tearsheet without it; their
    `harvest/trades.parquet` keeps every column, so the trades are taken from there.

    Returns:
        `harvest.read`'s dict, or the Spanish refusal.
    """
    got = load(identity, version)
    if isinstance(got, str):
        return got
    tear = got["tearsheet"]
    if isinstance(tear, str):
        return tear
    if "Size" not in tear["trades"]:
        trades = pd.read_parquet(Path(got["folder"]) / "harvest" / "trades.parquet", columns=TRADES)
        trades["Close type"] = trades["Close type"].astype(str)
        trades["sample"] = trades["sample"].astype(str)
        tear["trades"] = trades.sort_values("Close time", kind="stable")
    return tear | {"archived": got["version"]}


def harvest_folder(identity: str, version: str = "") -> Path | str:
    """The archived cosecha rows of this identity: `metrics`, `equity`, `trades` parquet."""
    got = load(identity, version)
    return got if isinstance(got, str) else Path(got["folder"]) / "harvest"


def _bank(shelf: dict, databank: str) -> dict:
    """One databank's entries of an archived shelf, whichever spelling was asked."""
    return next((v for k, v in shelf.items()
                 if k.replace(" ", "_") == databank.replace(" ", "_")), {})


def result(identity: str, databank: str, study: str, strategy: str, version: str = "") -> dict:
    """`/api/result` answered from the archive: the result archived for this study.

    Args:
        identity: The strategy's identity.
        databank: Either spelling.
        study: Study key.
        strategy: "" for the population result archived beside it.
        version: "" for the newest version.

    Returns:
        As `runs.result` served it on the day of archiving (its `stale` is that day's), or
        `{"error"}`.
    """
    got = load(identity, version)
    if isinstance(got, str):
        return {"error": got}
    held = _bank(got["results" if strategy else "populations"], databank).get(study)
    if held is None:
        return {"error": f"La versión {got['version']} del archivo no guarda {study} de {databank}."}
    return held


def history(identity: str, databank: str, study: str, strategy: str, version: str = "") -> dict:
    """`/api/history` from the archive: the single run it froze, in the live row shape."""
    held = result(identity, databank, study, strategy, version)
    if "error" in held or held["result"] is None:
        return {"runs": [], "skipped": []}
    r, meta = held["result"], held["meta"]
    said = r.get("verdict") or {}
    return {"runs": [{"day": meta["day"], "config_hash": meta["config_hash"],
                      "computed_at": meta["computed_at"], "state": said.get("state"),
                      "label": said.get("label"), "stale": meta["stale"]}], "skipped": []}


def matrix(identity: str, databank: str, version: str = "") -> dict:
    """`/api/matrix` from the archive: this identity's row only, as it stood that day."""
    got = load(identity, version)
    if isinstance(got, str):
        return {"error": got}
    cells = _bank(got["cells"], databank)
    name = got["tearsheet"]["strategy"] if isinstance(got["tearsheet"], dict) else ""
    return {"studies": catalogue.ordered(), "present": sorted(cells),
            "strategies": [{"strategy": name, "identity": identity}],
            "cells": {identity: cells}, "skipped": []}
