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


def cells(node: ET.Element) -> list[dict]:
    """One row per matrix cell: the parameters it settled on and how they did.

    Args:
        node: A `MatrixResult` element.

    Returns:
        `result` (SQX's own name for the cell), `oos_pct`, `runs`, the chosen `params`,
        and every stored statistic prefixed `is_` for the optimisation windows and `oos_`
        for the walk-forward windows -- 152 of each.
    """
    return [{"result": run.get("resultName"),
             "oos_pct": int(run.get("param1")), "runs": int(run.get("param2")),
             "params": _params(run.get("testParams"))}
            | {f"is_{k}": v for k, v in sqxstats.records(run.find("stats/SQStats").text).items()}
            | {f"oos_{k}": v
               for k, v in sqxstats.records(run.find("statsOOS/SQStats").text).items()}
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
