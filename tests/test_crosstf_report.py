#!/usr/bin/env python3
"""Cross TF's «Run solo esta estrategia» (owner, 2026-10-01): a one-mother run writes only that
mother's estrategias/<name>.json and never touches the population's verdict.csv,
cells.parquet or page — it used to replace them with that one mother, and the databank tab
lost the other 14. A whole-batch run still writes all three."""

import json
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.study import blocks, result as envelope
from studies.transfer.crossTF import report


def got(mothers: list[str]) -> dict:
    """What `many.run` returns, reduced to the parts `report.write` reads."""
    tab = envelope.tab("crossTF", "Cross-timeframe", [blocks.table("t", pd.DataFrame(
        {"mother": mothers}))])
    population = envelope.envelope("studies.transfer.crossTF", None, None, {}, time.time(),
                                   [tab])
    table = pd.DataFrame({"strategy": mothers, "identity": [None] * len(mothers),
                          "verdict": ["survives"] * len(mothers)})
    return {"population": population, "panel": pd.DataFrame({"mother": mothers}),
            "table": table, "nulls_seed": 1}


def test_one_mother_leaves_the_population_alone() -> None:
    """The population of 15 is written, then one mother is run alone: the 15 stay."""
    with tempfile.TemporaryDirectory() as tmp:
        out, export = Path(tmp) / "crossTF", Path(tmp) / "trades.parquet"
        export.write_bytes(b"")
        everyone = [f"Strategy 1.{i}" for i in range(15)]
        report.write(out, got(everyone), None, None, "all", export, "cmd", [])
        before = {f: (out / f).read_bytes() for f in ("verdict.csv", "cells.parquet",
                                                      "crossTF.json")}
        report.write(out, got(["Strategy 1.3"]), "abc", "Strategy 1.3", "one", export, "cmd",
                     [])
        assert {f: (out / f).read_bytes() for f in before} == before
        assert len(pd.read_csv(out / "verdict.csv")) == 15
        assert len(pd.read_parquet(out / "cells.parquet")) == 15
        member = json.loads((out / "estrategias" / "Strategy 1.3.json").read_text())
        assert member["strategy"] == "Strategy 1.3" and member["identity"] == "abc"


if __name__ == "__main__":
    test_one_mother_leaves_the_population_alone()
    print("ok")
