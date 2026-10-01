#!/usr/bin/env python3
"""Walk-Forward Matrix's «Run solo esta estrategia»: `--strategy` asks `many.one` for that
strategy alone and writes only estrategias/<name>.json; wfm.json, verdict.csv,
cell_correlations.csv, the manifest and every other strategy's JSON stay byte-identical."""

import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.study import blocks, result as envelope
from studies.optimisation.wfm import report

NAMES = ["Strategy 1.1.1", "Strategy 1.1.2", "Strategy 1.1.3"]
ASKED: list = []


def member(name: str) -> dict:
    """A contract result for one strategy."""
    return envelope.envelope("studies.optimisation.wfm", name, f"id-{name}", {}, time.time(),
                             [envelope.tab("m", "m", [blocks.table("t", pd.DataFrame(
                                 {"x": [1]}))])], blocks.verdict("blind", "watch", "m"))


def population(directory: Path, cfg: dict) -> dict:
    """many.run stand-in over three strategies."""
    return {"population": envelope.envelope("m", None, None, {}, time.time(), []),
            "members": [member(n) for n in NAMES],
            "table": pd.DataFrame({"strategy": NAMES, "identity": NAMES,
                                   "verdict": ["blind"] * 3, "rho": [0.0] * 3,
                                   "low": [0.0] * 3, "high": [0.0] * 3, "cells": [30] * 3,
                                   "share_changed": [0.5] * 3}),
            "cells": pd.DataFrame({"strategy": NAMES, "rho": [0.1, 0.2, 0.3]})}


def one(directory: Path, cfg: dict, strategy: str) -> dict:
    """many.one stand-in: records which strategy it was asked for."""
    ASKED.append(strategy)
    return member(strategy)


def files(folder: Path) -> dict[str, str]:
    """Every file under a folder, by its SHA-256."""
    return {f.relative_to(folder).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in folder.rglob("*") if f.is_file()}


def test_one_strategy_leaves_the_population_alone() -> None:
    """The export's report is written, then one strategy alone."""
    with tempfile.TemporaryDirectory() as tmp:
        export = Path(tmp) / "raw" / "wfm"
        export.mkdir(parents=True)
        report.config.export = lambda project, databank, day: export
        report.report_dir = lambda project, databank, day: Path(tmp) / "reports"
        report.many.run = population
        report.many.one = one
        base = ["report", "--project", "P", "--databank", "WFM"]
        sys.argv = base
        report.main()
        out = Path(tmp) / "reports" / "wfm"
        before = files(out)
        assert {"wfm.json", "verdict.csv", "cell_correlations.csv"} <= set(before)

        (out / "estrategias" / "Strategy 1.1.2.json").unlink()
        sys.argv = base + ["--strategy", "Strategy 1.1.2"]
        report.main()
        after = files(out)
        assert ASKED == ["Strategy 1.1.2"]
        assert set(after) == set(before)
        assert {k: v for k, v in after.items() if "1.1.2" not in k} \
            == {k: v for k, v in before.items() if "1.1.2" not in k}
        assert len(pd.read_csv(out / "verdict.csv")) == 3
        got = json.loads((out / "estrategias" / "Strategy 1.1.2.json").read_text())
        assert got["strategy"] == "Strategy 1.1.2" and got["identity"] == "id-Strategy 1.1.2"


if __name__ == "__main__":
    test_one_strategy_leaves_the_population_alone()
    print("ok")
