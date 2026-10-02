#!/usr/bin/env python3
"""Decay's «Run solo esta estrategia»: a one-strategy run writes only estrategias/<name>.json,
with the same numbers and verdict the population's verdict.csv gives it, and leaves decay.json,
verdict.csv and the manifest byte-identical."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.screening.decay import report

DAYS = pd.bdate_range("2014-01-01", "2022-12-31")


def curve(seed: int, drift: float) -> pd.Series:
    """A daily cumulative P&L with a known drift and noise."""
    rng = np.random.default_rng(seed)
    return pd.Series(np.cumsum(drift + rng.normal(0, 100, len(DAYS))), index=DAYS)


CURVES = {"Strategy 1.1.1": curve(1, 30.0), "Strategy 1.1.2": curve(2, 0.0),
          "Strategy 1.1.3": curve(3, -10.0)}


def files(folder: Path) -> dict[str, str]:
    """Every file directly in a folder, by its SHA-256."""
    return {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
            for f in folder.iterdir() if f.is_file()}


def test_one_strategy_leaves_the_population_alone() -> None:
    """Three strategies judged, then one alone: the population stays, its row matches."""
    with tempfile.TemporaryDirectory() as tmp:
        bank = Path(tmp) / "OOS"
        bank.mkdir()
        for name in CURVES:
            (bank / f"{name}.sqx").write_bytes(b"")
        report.databank_dir = lambda project, databank, install: bank
        report.report_dir = lambda project, databank, day: Path(tmp) / "reports" / day
        report.sqxstats.equity = lambda path: CURVES[path.stem]
        report.sqxfile.identity = lambda path: f"id-{path.stem}"
        base = ["report", "--project", "P", "--databank", "OOS", "--split", "2018-01-01",
                "--end", "2022-12-31"]
        sys.argv = base
        report.main()
        out = next((Path(tmp) / "reports").glob("*/decay"))
        before = files(out)
        assert set(before) >= {"decay.json", "verdict.csv", "manifest.json"}

        sys.argv = base + ["--strategy", "Strategy 1.1.2"]
        report.main()
        assert files(out) == before
        assert [p.name for p in (out / "estrategias").glob("*.json")] == ["Strategy 1.1.2.json"]
        got = json.loads((out / "estrategias" / "Strategy 1.1.2.json").read_text())
        row = pd.read_csv(out / "verdict.csv").set_index("strategy").loc["Strategy 1.1.2"]
        assert got["strategy"] == "Strategy 1.1.2" and got["identity"] == "id-Strategy 1.1.2"
        assert got["verdict"]["label"] == row["verdict"]
        assert abs(got["summary"]["t"] - row["t"]) < 1e-9
        assert abs(got["summary"]["sharpe_oos"] - row["sharpe_oos"]) < 1e-9


if __name__ == "__main__":
    test_one_strategy_leaves_the_population_alone()
    print("ok")
