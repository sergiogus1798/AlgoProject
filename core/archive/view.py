"""What the window is served today for one live strategy, captured so the archive can serve it again."""

from pathlib import Path

from ui.daemon import gateview
from ui.daemon.results import catalogue, matrix, runs
from ui.daemon.tearsheet import harvest


def results(project: str, identity: str, entries: list[dict]) -> dict:
    """Each study's result for the strategy, its population's, and its matrix cells.

    Args:
        project: SQX project name.
        identity: The strategy's identity.
        entries: What `collect.freeze` returned.

    Returns:
        `results` and `populations` as {databank: {study: `runs.result`}} — the newest day
        that judged the identity, and the population result of that same day — and
        `cells`, {databank: the matrix row of the identity}. A study that left only
        verdict.csv rows has `result` None, exactly as the live route answers. A folder
        that is not a catalogue study (`curate`) is frozen but has no route to serve.
    """
    newest = {(e["databank"], e["study"]): e for e in entries        # entries run oldest day first
              if e["study"] in catalogue.STUDIES}
    out = {"results": {}, "populations": {}, "cells": {}}
    for (databank, study), e in newest.items():
        name = e["named"] or e["names"][0]
        out["results"].setdefault(databank, {})[study] = runs.result(
            project, databank, study, name, identity, "")
        out["populations"].setdefault(databank, {})[study] = runs.result(
            project, databank, study, "", "", e["day"])
    for databank in sorted({databank for databank, _ in newest}):
        out["cells"][databank] = matrix.matrix(project, databank)["cells"].get(identity, {})
    return out


def tearsheet(project: str, databank: str, identity: str, out: Path) -> dict | str:
    """The cosecha rows the Ficha is built from, as `harvest.read` serves them.

    Args:
        project: SQX project name.
        databank: The build databank, as its harvest folder spells it.
        identity: The strategy's identity.
        out: `<version>/tearsheet/`, where the two frames are written as parquet.

    Returns:
        `harvest.read` without its two frames (they are on disk), or its Spanish refusal.
    """
    got = harvest.read(project, databank, identity)
    if isinstance(got, str):
        return got
    out.mkdir()
    got.pop("equity").to_parquet(out / "equity.parquet")
    got.pop("trades").to_parquet(out / "trades.parquet")
    return got


def gate(project: str, databank: str, identity: str, day: str) -> dict | None:
    """The gate's report as the gate zone serves it, cut to this strategy's row, and its sheet.

    Args:
        project: SQX project name.
        databank: The build databank.
        identity: The strategy's identity.
        day: The harvest day the Ficha read.

    Returns:
        `report` — `gateview.gate` with `rows` holding only this identity — and `strategy`,
        `gateview.strategy`; None when no gate report judged that harvest.
    """
    folder = harvest.newest(project, databank)
    report_day, _ = gateview.judged(folder)
    if not report_day:
        return None
    report = gateview.gate(project, databank, report_day)
    report["rows"] = [r for r in report["rows"] if r["identity"] == identity]
    return {"report_day": report_day, "report": report,
            "strategy": gateview.strategy(project, databank, day, identity)}
