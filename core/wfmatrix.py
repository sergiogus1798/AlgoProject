"""Read the Walk-Forward Matrix a WFM cross-check leaves inside a .sqx, without SQX running."""

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from core import sqxstats

# SQX writes the matrix axes as two ranges: param1 is the out-of-sample percentage and
# param2 the number of walk-forward runs. periodType 10 is a rolling window: measured on
# XAUUSD/WFM, IS stays at 4.72 years and OOS at 1.33 and both slide -- neither expands.
AXES = {"oos_pct": ("start1", "stop1", "increment1"), "runs": ("start2", "stop2", "increment2")}
MILLIS = 1000
# A cell's own result stores 15 SQStats blobs: direction (0 both, 1 long, -1 short) x sample.
# Measured on XAUUSD/WFM: sample 10 is the first optimisation window alone, 20 every walk-forward
# run concatenated, and 127 the two together -- trades and days add up exactly. Direction 0 is the
# one every study here wants; the long/short split is in the file for whoever needs it.
SAMPLES = {"is": 10, "oos": 20, "all": 127}
BLOB = "ValuesMap/stats_LQ1_direction_DD_{d}_L1_pl_DD_10_L1_sample_DD_{s}_L1__RQ1_/SQStats"


def _params(text: str) -> dict:
    """Split SQX's `Name=value,` parameter string.

    Args:
        text: A `testParams` or `testParameters` attribute.

    Returns:
        Parameter name to value, values kept as text because a parameter may be integer,
        float or an enum label and the study must not guess which.
    """
    return dict(pair.split("=", 1) for pair in text.split(",") if pair)


def _seconds(node: ET.Element, attr: str) -> int:
    """Args:
        node: The element carrying the timestamp.
        attr: Attribute name holding epoch milliseconds.

    Returns:
        Epoch seconds, the unit every other table in this project uses.
    """
    return int(node.get(attr)) // MILLIS


def _stats(node: ET.Element, holder: str) -> dict:
    """Args:
        node: A `WalkForwardPeriod` element.
        holder: `OptimizationStats` or `RunStats`.

    Returns:
        The 152 stored statistics, or nothing at all. A cell's last step is optimised but
        never run -- there is no data past the end of the history -- so SQX writes an empty
        `RunStats`. Those steps carry no `oos_` columns and must be dropped, not zero-filled.
    """
    blob = node.find(f"{holder}/stats/SQStats")
    return {} if blob is None else sqxstats.records(blob.text)


def _cell_stats(result: ET.Element, direction: int = 0) -> dict:
    """Args:
        result: One `<Result>` element of the strategy's ResultsMap.
        direction: 0 for both sides, 1 long only, -1 short only.

    Returns:
        The 152 statistics prefixed `is_`, `oos_` and `all_`. Read from the result's own
        sample-typed blobs, not from `RunResult/stats` -- that one is the full period
        despite sitting next to a field called `statsOOS`, and reading it as in-sample
        silently turns the composite into the optimisation window.
    """
    return {f"{name}_{k}": v for name, sample in SAMPLES.items()
            for k, v in sqxstats.records(
                result.find(BLOB.format(d=direction, s=sample)).text).items()}


def results(path: Path) -> dict[str, ET.Element]:
    """Args:
        path: A .sqx file.

    Returns:
        Result key to its `<Result>` element -- the main backtest plus one per matrix cell,
        keyed exactly as `RunResult/@resultName` names them.
    """
    xml = zipfile.ZipFile(path).read("settings.xml").decode("utf8", errors="replace")
    return {r.get("resultKey"): r for r in ET.fromstring(xml).find("ResultsMap/Results")}


def matrix(path: Path) -> ET.Element | None:
    """Args:
        path: A .sqx file.

    Returns:
        The `MatrixResult` element, or nothing when the strategy never went through a
        Walk-Forward Matrix cross-check -- a databank holds both, and a stripped copy of
        a strategy carries the rules without any cross-check result.
    """
    xml = zipfile.ZipFile(path).read("settings.xml").decode("utf8", errors="replace")
    found = ET.fromstring(xml).find(".//WalkForwardResult")
    return None if found is None else found[0]


def axes(node: ET.Element) -> dict:
    """Args:
        node: A `MatrixResult` element.

    Returns:
        `oos_pct` and `runs` as (first, last, step), plus `period_type`. The cell count is
        the product of the two ranges -- 5 x 6 = 30 on the XAUUSD/WFM databank.
    """
    out = {name: tuple(int(node.get(a)) for a in attrs) for name, attrs in AXES.items()}
    return out | {"period_type": int(node.get("periodType"))}


def cells(node: ET.Element, found: dict[str, ET.Element]) -> list[dict]:
    """One row per matrix cell: the parameters it settled on and how they did.

    Args:
        node: A `MatrixResult` element.
        found: Output of `results` for the same strategy.

    Returns:
        `result` (SQX's own name for the cell), `oos_pct`, `runs`, the chosen `params`, the
        two fitness values SQX scored the cell with, and every stored statistic three times:
        `is_` for the first optimisation window, `oos_` for the walk-forward runs
        concatenated, `all_` for both together.
    """
    return [{"result": run.get("resultName"),
             "oos_pct": int(run.get("param1")), "runs": int(run.get("param2")),
             "params": _params(run.get("testParams")),
             "fitness_is": float(found[run.get("resultName")].find("Fitnesses").get("IS")),
             "fitness_oos": float(found[run.get("resultName")].find("Fitnesses").get("OOS"))}
            | _cell_stats(found[run.get("resultName")])
            for run in node.findall("RunResult")]


def periods(node: ET.Element) -> list[dict]:
    """One row per walk-forward step of every cell -- the table a correlation study needs.

    Args:
        node: A `MatrixResult` element.

    Returns:
        The cell keys, the step's `index`, its optimisation and run windows as epoch
        seconds, the `params` the optimiser picked on that window, and the same 152
        statistics twice: `is_` from OptimizationStats, `oos_` from RunStats.

        The last step of every cell is `future`: SQX optimises it but there is no data to
        run it on, so it carries no `oos_` columns at all and must be dropped before any
        correlation is taken.
    """
    return [{"result": run.get("resultName"),
             "oos_pct": int(run.get("param1")), "runs": int(run.get("param2")),
             "index": i,
             "optimize_from": _seconds(p, "optimizeFrom"),
             "optimize_to": _seconds(p, "optimizeTo"),
             "run_from": _seconds(p, "runFrom"), "run_to": _seconds(p, "runTo"),
             "future": p.get("futurePeriod") == "true",
             "params": _params(p.get("testParameters"))}
            | {f"is_{k}": v for k, v in _stats(p, "OptimizationStats").items()}
            | {f"oos_{k}": v for k, v in _stats(p, "RunStats").items()}
            for run in node.findall("RunResult")
            for i, p in enumerate(run.findall("Periods/WalkForwardPeriod"))]
