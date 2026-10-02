#!/usr/bin/env python3
"""MC Retest's «Run solo esta estrategia»: `--strategy` takes the databank's «Strategy 1.2.3» or
the ingest's «1.2.3», runs `one.run` on that strategy alone (its own trades only), writes only
estrategias/<name>.json and leaves mcRetest.json, verdict.csv, the manifest and every other
strategy's JSON byte-identical; a strategy missing a task that ran is refused."""

import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.study import blocks, result as envelope
from studies.breakage.mcRetest import report

NAMES = ["1.2.3", "1.2.4", "1.2.5"]
SEEN: list = []


def member(name: str) -> dict:
    """A contract result for one strategy, with the summary row many.table reads."""
    return envelope.envelope(
        "studies.breakage.mcRetest", name, f"id-{name}", {}, time.time(),
        [envelope.tab("t", "t", [blocks.table("t", pd.DataFrame({"x": [1]}))])],
        blocks.verdict("FAIL", "fail", "m"),
        summary={"verdict": "FAIL", "composite": float(len(name)), "binding": "x",
                 "stress_net_p5": 0.0, "stress_cvar_dd_pct": 0.0, "vetoes": "",
                 "blocked_by": ""})


def inputs(project: str, databank: str, day: str) -> dict:
    """An ingest of three strategies; 1.2.5 lacks the `stress` task."""
    sims = pd.DataFrame([(t, n) for n in NAMES for t in ("bar", "stress")
                         if (n, t) != ("1.2.5", "stress")], columns=["task", "strategy"])
    return {"sims": sims, "folder": Path(tempfile.gettempdir()), "identity": {},
            "trades": pd.DataFrame({"strategy": NAMES, "pnl": [1.0, 2.0, 3.0]})}


def one(name: str, got: dict, cfg: dict) -> dict:
    """one.run stand-in: records the trades it was handed."""
    SEEN.append(got["trades"])
    return member(name)


def files(folder: Path) -> dict[str, str]:
    """Every file under a folder, by its SHA-256."""
    return {f.relative_to(folder).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in folder.rglob("*") if f.is_file()}


def test_one_strategy_leaves_the_population_alone() -> None:
    """The ingest's report is written, then 1.2.4 alone under either spelling."""
    with tempfile.TemporaryDirectory() as tmp:
        report.report_dir = lambda project, databank, day: Path(tmp) / day
        report.load.load = inputs
        report.many.run = lambda got, cfg: {
            "members": [member(n) for n in NAMES],
            "population": envelope.envelope("m", None, None, {}, time.time(), [])}
        report.one.run = one
        base = ["report", "--project", "P", "--day", "2026-09-30"]
        sys.argv = base
        report.main()
        out = Path(tmp) / "2026-09-30" / "mcRetest"
        before = files(out)
        assert "verdict.csv" in before and "estrategias/1.2.4.json" in before

        for spelling in ("Strategy 1.2.4", "1.2.4"):
            sys.argv = base + ["--strategy", spelling]
            report.main()
            after = files(out)
            assert {k: v for k, v in after.items() if not k.startswith("estrategias/1.2.4.")} \
                == {k: v for k, v in before.items() if not k.startswith("estrategias/1.2.4.")}
            assert set(after) == set(before)
            assert SEEN[-1]["strategy"].tolist() == ["1.2.4"]
        assert len(pd.read_csv(out / "verdict.csv")) == 3
        assert json.loads((out / "estrategias" / "1.2.4.json").read_text())["strategy"] == "1.2.4"

        sys.argv = base + ["--strategy", "Strategy 1.2.5"]
        try:
            report.main()
            raise AssertionError("1.2.5 lacks a task and was not refused")
        except SystemExit as e:
            assert "stress" in str(e)


if __name__ == "__main__":
    test_one_strategy_leaves_the_population_alone()
    print("ok")
