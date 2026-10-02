#!/usr/bin/env python3
"""Golden and refusal tests for step 6: the Build's acceptance filters from a `_study.yaml`.

`sqx.projects.rankings.set_rankings` must replace the donor's `<Rankings>` conditions — all of
them, and only them: the `<BuildMode>` conditions, which come first in a Build task, stay — with
the ones `core.buildfilters.filters` resolves, every one read on sampleType 10. A missing value
is a refusal, never a default.
"""

import re
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.assetdata import load
from core.buildfilters import filters
from core.datapaths import projects_backup
from sqx.projects import rankings

FIXTURES = Path(__file__).resolve().parent / "fixtures/build_acceptance"
STUDY = FIXTURES / "study.yaml"
DONOR = projects_backup("XAUUSD_base_2026-09-21") / "project.cfx"
BUILD = "Build-Task3.xml"
FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    """Record one assertion without stopping the run."""
    print(f"  {'ok ' if ok else 'FAIL'} {label}")
    if not ok:
        FAILURES.append(f"{label} {detail}")


def refuses(label: str, text: str, symbol: str, timeframe: str, mode: str = "study") -> None:
    """A study file with this text must stop `filters` with a SystemExit."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "study.yaml"
        if text is not None:
            path.write_text(text, encoding="utf-8")
        try:
            filters(load(symbol), timeframe, mode, path)
            check(label, False, "no refusal")
        except SystemExit:
            check(label, True)


def conditions_of(text: str) -> str:
    """The `<Conditions>` element inside `<Rankings>`."""
    block = rankings.RANKINGS.search(text).group(0)
    return rankings.CONDITIONS.search(block).group(0)


def main() -> None:
    """Run every check and exit non-zero on any failure."""
    with zipfile.ZipFile(DONOR) as z:
        donor = z.read(BUILD).decode("utf-8")
    for mode in ("study", "calibration"):
        written = filters(load("XAUUSD"), "H1", mode, STUDY)
        out = rankings.set_rankings(donor, written["conditions"])
        golden = FIXTURES / f"rankings_XAUUSD_H1_{mode}.xml"
        if "--update" in sys.argv:
            golden.write_text(conditions_of(out), encoding="utf-8")
        check(f"{mode}: golden conditions", conditions_of(out) == golden.read_text("utf-8"))
        check(f"{mode}: donor's Sortino and Stagnation gone from <Rankings>",
              "SortinoRatio" not in conditions_of(out) and "Stagnation" not in conditions_of(out))
        check(f"{mode}: every condition reads sampleType 10",
              conditions_of(out).count('sampleType="10"') == len(written["conditions"])
              and 'sampleType="127"' not in conditions_of(out))
        mode_block = re.search(r"<BuildMode.*?</BuildMode>", donor, re.S).group(0)
        check(f"{mode}: <BuildMode> conditions untouched", mode_block in out)
        check(f"{mode}: nothing else of the task changed",
              out.replace(conditions_of(out), "") == donor.replace(conditions_of(donor), ""))
    check("study: totals are per-year x the build's 10 years",
          rankings.describe(filters(load("XAUUSD"), "H1", "study", STUDY)) ==
          "study @IS: NumberOfTrades >= 300 & NumberOfTrades <= 750 & ProfitFactor >= 1.2 "
          "& NetProfit > 0")
    check("override: DAX40 takes its own PF and timeframe, over its 6.25-year build",
          rankings.describe(filters(load("DAX40"), "H4", "study", STUDY)) ==
          "study @IS: NumberOfTrades >= 125 & NumberOfTrades <= 312 & ProfitFactor >= 1.25 "
          "& NetProfit > 0")
    text = STUDY.read_text(encoding="utf-8")
    refuses("refuses: no file", None, "XAUUSD", "H1")
    refuses("refuses: timeframe without trades_per_year", text, "XAUUSD", "M30")
    refuses("refuses: no profit_factor_min", text.replace("  profit_factor_min: 1.20\n", ""),
            "XAUUSD", "H1")
    refuses("refuses: a ceiling missing", text.replace("H1: {min: 30, max: 75}", "H1: {min: 30}"),
            "XAUUSD", "H1")
    refuses("refuses: a sample that is not IS", text.replace("sample: IS", "sample: OOS"),
            "XAUUSD", "H1")
    refuses("refuses: calibration without its block", text.split("calibration:")[0],
            "XAUUSD", "H1", "calibration")
    if FAILURES:
        raise SystemExit("\n".join(FAILURES))
    print("all ok")


if __name__ == "__main__":
    main()
