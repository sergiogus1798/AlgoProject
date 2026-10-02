#!/usr/bin/env python3
"""The trade Monte Carlo's «Run solo esta estrategia»: `--strategy` runs `one.run` on that
strategy alone and writes only estrategias/<name>.json; monteCarlo.json, verdict.csv, flags.csv,
the manifest and every other strategy's JSON stay byte-identical, an unknown name is refused,
and `--strategy` with `--portfolio` is refused."""

import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.study import blocks, result as envelope
from portfolio.common.monteCarlo import many, report

NAMES = ["Strategy 1.1.1", "Strategy 1.1.2", "Strategy 1.1.3"]
RAN: list = []


def member(name: str) -> dict:
    """A contract result for one strategy, with the summary row many.table reads."""
    summary = {c: 0.0 for c in many.COLUMNS} | {"tier": "FAIL", "fired": [], "gates": 1}
    return envelope.envelope("portfolio.common.monteCarlo", name, f"id-{name}", {},
                             time.time(), [envelope.tab("m", "m", [blocks.table(
                                 "t", pd.DataFrame({"x": [1]}))])],
                             blocks.verdict("FAIL", "fail", "m"), summary=summary)


def one(name: str, inputs: dict, cfg: dict) -> dict:
    """one.run stand-in: records which strategy it ran."""
    RAN.append(name)
    return member(name)


def files(folder: Path) -> dict[str, str]:
    """Every file under a folder, by its SHA-256."""
    return {f.relative_to(folder).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in folder.rglob("*") if f.is_file()}


def test_one_strategy_leaves_the_population_alone() -> None:
    """The databank's report is written, then one strategy alone."""
    with tempfile.TemporaryDirectory() as tmp:
        export = Path(tmp) / "trades.parquet"
        export.write_bytes(b"")
        report.report_dir = lambda project, databank, day: Path(tmp) / "reports"
        report.assets.report = lambda asset: asset
        report.load.load = lambda *a: {"streams": dict.fromkeys(NAMES), "reference": NAMES[0],
                                       "shared": {"export": export}}
        report.many.run = lambda inputs, cfg: {
            "members": [member(n) for n in NAMES],
            "population": envelope.envelope("m", None, None, {}, time.time(), [])}
        report.one.run = one
        base = ["report", "--project", "P", "--databank", "WFM", "--asset", "USDJPY"]
        sys.argv = base
        report.main()
        out = Path(tmp) / "reports" / "monteCarlo"
        before = files(out)
        assert {"monteCarlo.json", "verdict.csv", "flags.csv", "manifest.json"} <= set(before)

        (out / "estrategias" / "Strategy 1.1.3.json").unlink()
        sys.argv = base + ["--strategy", "Strategy 1.1.3"]
        report.main()
        after = files(out)
        assert RAN == ["Strategy 1.1.3"]
        assert set(after) == set(before)
        assert {k: v for k, v in after.items() if "1.1.3" not in k} \
            == {k: v for k, v in before.items() if "1.1.3" not in k}
        assert len(pd.read_csv(out / "verdict.csv")) == 3
        got = json.loads((out / "estrategias" / "Strategy 1.1.3.json").read_text())
        assert got["strategy"] == "Strategy 1.1.3"

        for extra in (["--strategy", "Strategy 9.9.9"],
                      ["--strategy", "Strategy 1.1.1", "--portfolio"]):
            sys.argv = base + extra
            try:
                report.main()
                raise AssertionError(f"{extra} was not refused")
            except SystemExit:
                pass
        assert RAN == ["Strategy 1.1.3"] and files(out) == after


if __name__ == "__main__":
    test_one_strategy_leaves_the_population_alone()
    print("ok")
