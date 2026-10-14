"""SQX's Walk-Forward Matrix objectives per cell — stability, score, the WF specials — and its rule."""

import math
import xml.etree.ElementTree as ET
from typing import Any

from core import sqxstats
from core.xmlget import attr as _at, el as _el, text as _tx

# Decoded from SQX (knowhow/conditions/wfm-acceptance.md): none of these three families is
# stored; SQX recomputes them from the steps every time it paints. Reproduced here and
# checked equal to SQX's own databank export, 14 columns on 17 strategies (2026-10-01).
FAMILY = {30: "oos", 31: "stability", 32: "score", 33: "special"}
SAMPLE = {10: "is", 20: "oos", 127: "all"}
SPECIALS = ("WFPctOfProfitableRuns", "WFMaxProfitByRunInPct", "WFMinTradesInRun",
            "WFMaxPctDDbyRun", "WFMaxDDbyRun", "WFMaxProfitByRun", "WFMaxStagnationInPct")
# `setDependentOnTradingPeriod(true)` in SQX's column sources: stability divides them by days
# first, so a 3-year window and a 1-year one compare rates, not totals.
PER_DAY = {"AvgPctDrawdown", "Commission", "DrawdownPips", "OpenDrawdown", "AvgDrawdown",
           "OpenDrawdownPct", "NetProfit", "Drawdown", "MaxNewHighDuration", "NetProfitInPips",
           "SlippageInMoney", "NumberOfTrades", "NumberOfProfits", "NumberOfLosses",
           "NetProfitInPct", "Stagnation"}
# Integer-format columns: SQX truncates their stability and score (111.96 reads 111).
INTEGER = {"AmbiguousTrades", "MaxConsecLosses", "MaxConsecWins", "NumberOfProfits",
           "NumberOfCanceled", "DegreesOfFreedom", "Complexity", "MaxNewHighDuration",
           "TotalTradingMonths", "ProfitableMonths", "LongestTrade", "NumberOfLosses",
           "NumberOfTrades", "TotalTradingDays", "TotalDataYears", "TotalDataMonths",
           "TotalDataDays", "Stagnation", "TotalTradingYears"}
# What the window shows for every cell whatever the conditions were. Stability of NetProfit
# is Pardo's walk-forward efficiency: OOS profit per day over IS profit per day.
SHOWN = ([("stability", m) for m in ("NetProfit", "ProfitFactor", "SharpeRatio", "DrawdownPct",
                                     "NumberOfTrades")]
         + [("score", m) for m in ("NetProfit", "ProfitFactor", "SharpeRatio", "DrawdownPct")]
         + [("special", m) for m in SPECIALS])
OPS = {">": float.__gt__, "<": float.__lt__, ">=": float.__ge__, "<=": float.__le__,
       "=": float.__eq__, "==": float.__eq__}
BLOB = "ValuesMap/stats_LQ1_direction_DD_0_L1_pl_DD_10_L1_sample_DD_{s}_L1__RQ1_/SQStats"
DAY_MS = 86_400_000


def _round2(x: float) -> float:
    """SQUtils.round(x, 2): half up, not Python's half to even."""
    return math.floor(x * 100 + 0.5) / 100


def _ratio(a: float, b: float) -> float:
    """SQUtils.safeDivide: zero when the divisor is."""
    return 0.0 if b == 0 else a / b


def _days(p: ET.Element, start: str, end: str) -> int:
    """Whole days between two of a step's epoch-millisecond bounds, floored like SQTime."""
    return (int(_at(p, end)) - int(_at(p, start))) // DAY_MS


def rule(root: ET.Element) -> tuple[dict[str, int], list[dict[str, Any]]]:
    """The criterion the WFM ran with, as the strategy itself stores it.

    Args:
        root: A .sqx `settings.xml` root.

    Returns:
        `threshold_pct`, `rows`, `cols`, `min_squares`, and the active conditions in their
        order: `family`, `metric`, `sample`, `op`, `value`. A WF special is a special even
        under subresult 30 — the master's conditions carry it that way and SQX forces it.
    """
    node = _el(root.find("SpecialValuesMap/SettingsMap/WalkForwardConditions/Conditions"))
    conds = []
    for c in node.findall("Condition"):
        if c.get("use") != "true":
            continue
        col = _el(c.find("Left-Side/Column-Value"))
        metric = _at(col, "column")
        conds.append({"family": "special" if metric in SPECIALS
                      else FAMILY[int(_at(col, "subresult"))],
                      "metric": metric, "sample": SAMPLE[int(_at(col, "sampleType"))],
                      "op": _at(_el(c.find("Comparator")), "value"),
                      "value": float(_at(_el(c.find("Right-Side/Numeric-Value")), "value"))})
    return ({"threshold_pct": int(_at(node, "thresholdPct")), "rows": int(_at(node, "robCombRows")),
             "cols": int(_at(node, "robCombCols")), "min_squares": int(_at(node, "robMinComb"))},
            conds)


def _stability(steps: list[ET.Element], metric: str) -> float:
    """Σ run-window metric over Σ optimisation-window metric, ×100, last step left out."""
    opt = run = 0.0
    for p in steps[:-1]:
        opt += sqxstats.records(_tx(p.find("OptimizationStats/stats/SQStats")))[metric]
        blob = p.find("RunStats/stats/SQStats")
        run += 0.0 if blob is None else sqxstats.records(_tx(blob))[metric]
    if metric in PER_DAY:
        opt = _ratio(opt, sum(_days(p, "optimizeFrom", "optimizeTo") for p in steps[:-1]))
        run = _ratio(run, sum(_days(p, "runFrom", "runTo") for p in steps[:-1]))
    return _round2(_ratio(run, opt) * 100)


def _special(steps: list[ET.Element], metric: str) -> float:
    """SQX's `Columns/WalkForward` snippets, over the steps that ran."""
    runs = [None if (blob := p.find("RunStats/stats/SQStats")) is None
            else sqxstats.records(_tx(blob)) for p in steps]
    if runs[0] is None:
        return 0.0
    live = [r for r in runs if r is not None]
    if metric == "WFPctOfProfitableRuns":
        n = len(steps) - 1
        return sum(r is not None and r["NetProfit"] > 0 for r in runs[:n]) / (n / 100)
    if metric == "WFMaxProfitByRunInPct":
        top, total = max(r["NetProfit"] for r in live), sum(r["NetProfit"] for r in live)
        return 100.0 if top > 0 and total < 0 else top / (total / 100)
    if metric == "WFMinTradesInRun":
        return float(min(r["NumberOfTrades"] for r in live))
    key = {"WFMaxPctDDbyRun": "DrawdownPct", "WFMaxDDbyRun": "Drawdown",
           "WFMaxProfitByRun": "NetProfit", "WFMaxStagnationInPct": "StagnationPct"}[metric]
    return max(r[key] for r in live)


def value(run: ET.Element, cell: ET.Element, base: dict[str, float], family: str, metric: str,
          sample: str = "all") -> float:
    """One objective of one cell, as SQX computes it.

    Args:
        run: The cell's `RunResult`.
        cell: The cell's own `<Result>`.
        base: The main backtest's statistics, sample 127 — what `score` divides by.
        family: `oos`, `stability`, `score` or `special`.
        metric: SQX's column name.
        sample: For `oos`, which of the cell's samples: `is`, `oos` or `all`.
    """
    steps = run.findall("Periods/WalkForwardPeriod")
    if family == "oos":
        code = {v: k for k, v in SAMPLE.items()}[sample]
        return float(sqxstats.records(_tx(cell.find(BLOB.format(s=code))))[metric])
    if family == "special":
        return _special(steps, metric)
    got = (_stability(steps, metric) if family == "stability" else
           _round2(sqxstats.records(_tx(run.find("stats/SQStats")))[metric] / (base[metric] / 100)))
    return float(math.trunc(got)) if metric in INTEGER else got


def cells(root: ET.Element) -> tuple[dict[str, int], list[dict[str, Any]], list[dict[str, Any]]]:
    """Every cell of one strategy against its own criterion, and the `SHOWN` objectives.

    Args:
        root: A .sqx `settings.xml` root holding a Walk-Forward Matrix result.

    Returns:
        The rule, one row per (cell, condition) — `condition` its position, `met` whether
        it holds — and one row per cell with `stability_`/`score_`/`special_` columns and
        `param_stability`, SQX's stored parameter-stability of that cell.
    """
    the_rule, conds = rule(root)
    found = {_at(r, "resultKey"): r for r in _el(root.find("ResultsMap/Results"))}
    main = next(k for k in found if not k.startswith("WF"))
    base = sqxstats.records(_tx(found[main].find(BLOB.format(s=127))))
    special = _el(root.find("SpecialValuesMap/SettingsMap"))
    checked, shown = [], []
    for run in _el(root.find(".//WalkForwardResult"))[0].findall("RunResult"):
        key = _at(run, "resultName")
        where = {"result": key, "oos_pct": int(_at(run, "param1")), "runs": int(_at(run, "param2"))}
        for i, c in enumerate(conds):
            got = value(run, found[key], base, c["family"], c["metric"], c["sample"])
            # `value` was the threshold in `c`; from here on it is the cell's own number.
            checked.append(where | c | {"condition": i, "threshold": c["value"], "value": got,
                                        "met": OPS[c["op"]](got, c["value"])})
        stab = special.find(f"ParametersStability_WF_{where['runs']}_runs_{where['oos_pct']}_OOS")
        shown.append(where | {f"{f}_{m}": value(run, found[key], base, f, m) for f, m in SHOWN}
                     | {"param_stability": None if stab is None else float(_tx(stab))})
    return the_rule, checked, shown
