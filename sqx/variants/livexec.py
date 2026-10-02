"""`execute`'s load, run, panel, sync and clear on a live GUI session (`sqx.projects.live`), no restart."""

import csv
import sys
import time
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

from sqx.projects import live, stage
from sqx.variants import legs as legmod


def backend(cfg: dict) -> ModuleType:
    """This module when this holder's GUI session is up on the batch's worker, else `execute`."""
    from sqx.variants import execute
    return sys.modules[__name__] if live.mine(cfg["role"]) else execute


def awake(cfg: dict) -> bool:
    """The session is up and is not this call's to stop."""
    return False


def _banks() -> list[str]:
    """The batch's input and the three legs' outputs."""
    return [legmod.source()] + [leg["databank"] for leg in legmod.legs()]


def clear(cfg: dict) -> int:
    """Empty the four databanks in memory and on disk; how many strategies went."""
    gone = 0
    for bank in _banks():
        n = live.records(cfg["role"], cfg["project"])[bank]
        if n:
            gone += live.cut(cfg["role"], cfg["project"], bank,
                             live.call(cfg["role"], "listStrategies", projectName=cfg["project"],
                                       databankName=bank)["strategies"])
    return gone


def load(folder: Path, cfg: dict) -> None:
    """Empty the four databanks, then put the batch into the input and wait until it is all in."""
    clear(cfg)
    want = len(list(folder.glob("*.sqx")))
    live.call(cfg["role"], "loadFilesToDatabank", projectName=cfg["project"],
              databankName=legmod.source(), folder=str(folder), clear="true", all="true")
    for _ in range(1200):
        if live.records(cfg["role"], cfg["project"])[legmod.source()] == want:
            return
        time.sleep(0.5)
    raise SystemExit(f"{legmod.source()}: no llegaron las {want} variantes en 10 min")


def run(expected: int, cfg: dict, progress: Callable[[int, str], None]) -> int:
    """Run the three legs, and only them (sent as the start's projectXML), and wait.

    Returns:
        What the three legs returned between them, as `execute.run` counts it.
    """
    xml = live.call(cfg["role"], "getConfig", projectName=cfg["project"])["config"]["xml"]
    config = stage.only(xml, [leg["title"] for leg in legmod.legs()])[0]
    progress(0, f"{expected} retests lanzados")
    end = live.run(cfg["role"], cfg["project"], config)
    if "Error" in end:
        raise SystemExit(f"SQX: {end}")
    mem = live.records(cfg["role"], cfg["project"])
    return sum(mem[leg["databank"]] for leg in legmod.legs())


def panel(out: Path, cfg: dict, databank: str, stem: str) -> Path:
    """The leg's rows in its view's column order (`loadGridData`, no header): nothing reads it."""
    rows = live.call(cfg["role"], "loadGridData", projectName=cfg["project"], databankName=databank,
                     first1000="false", lastChangeTime="0", refreshAction="false")["gridData"]
    path = out / f"{stem}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        csv.writer(f, delimiter=";").writerows(rows)
    return path


def synced(expected: int, cfg: dict, databank: str) -> tuple[Path, int]:
    """Mirror one leg onto disk; its folder and how many `.sqx` it holds."""
    live.sync(cfg["role"], cfg["project"], [databank])
    folder = legmod.bank_dir(cfg["role"], cfg["project"], databank)
    return folder, len(list(folder.glob("*.sqx")))
