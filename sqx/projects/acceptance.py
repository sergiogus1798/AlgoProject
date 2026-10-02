#!/usr/bin/env python3
"""Write a cross-check's acceptance element: the conditions it judges by, and their thresholds."""

import re

CONDITIONS = re.compile(r"<Conditions\b([^>]*?)(?:/>|>.*?</Conditions>)", re.S)
ESCAPED = {">": "&gt;", "<": "&lt;", ">=": "&gt;=", "<=": "&lt;=", "=": "=", "<>": "&lt;&gt;"}
# Where a condition reads its number from, per family: subresult, sampleType and the
# columnType SQX writes beside it. 🔬 Decompiled 2026-09-24 from
# WalkForwardCrossCheckMethod.getStatsValue: `subresult` picks the blob, and only family 30
# looks at `sampleType` -- 20 is every walk-forward run concatenated, which is the only
# sample a walk-forward cell can be judged on. The other three read statsStability,
# statsScore and statsSpecial, which are computed per cell and carry no samples at all.
READS = {"is": (30, 10, "0", "Decimal2"),     # the task's own backtest, in-sample only
         "oos": (30, 20, "0", "Decimal2"),
         "stability": (31, 127, "0", "Decimal2Pct"),
         "score": (32, 127, "0", "Decimal2Pct"),
         "special": (33, 127, "33", "Decimal2Pct")}
FORMATS = {"NetProfit": "Decimal2PL", "WFMinTradesInRun": "Integer", "NumberOfTrades": "Integer"}


def condition(spec: dict, crosscheck: str) -> str:
    """One `<Condition>` element, in the shape SQX's own recommended set writes.

    Args:
        spec: One entry of a catalogue's `conditions` list -- `read` (a key of READS),
            `metric` (the column class, e.g. ProfitFactor or WFPctOfProfitableRuns), `op`
            and `value`.
        crosscheck: Element name the condition is evaluated by, e.g. "WalkForwardMatrix";
            "main" for the task's own backtest (a Build's `<Rankings>`, read "is").
            It is not decoration: SQX looks the cross-check up by this name and asks it for
            the value, so a condition naming a cross-check the install does not have
            evaluates to nothing.

    Returns:
        The element as text, active.
    """
    subresult, sample, column_type, default = READS[spec["read"]]
    metric = spec["metric"]
    return (f'<Condition use="true"><Left-Side valueType="column"><Column-Value '
            f'column="{metric}" columnType="{column_type}" '
            f'format="{FORMATS.get(metric, default)}" resultType="{crosscheck}" '
            f'direction="0" sampleType="{sample}" plType="10" confidenceLevel="50" '
            f'market="1" subresult="{subresult}" pctRatio="0" class="{metric}"/>'
            f'</Left-Side><Comparator value="{ESCAPED[spec["op"]]}"/>'
            f'<Right-Side valueType="numeric"><Numeric-Value value="{spec["value"]}"/>'
            f'</Right-Side></Condition>')


def area(rows: int, cols: int, size: int, minimum: int, threshold_pct: int) -> dict:
    """The Walk Forward Matrix's own acceptance attributes, checked against the grid.

    Args:
        rows, cols: The matrix's shape -- numbers of passes by out-of-sample percentages.
        size: Side of the rectangle SQX slides over the matrix looking for an area of cells
            that passed.
        minimum: How many of that rectangle's cells must have passed for the strategy to be
            accepted. 0 never rejects anybody, which turns the cross-check back into a map.
        threshold_pct: Percentage of a cell's active conditions that must hold for the cell
            itself to count as passed.

    Returns:
        The attributes of the `<Conditions>` element.

    Raises:
        SystemExit: The rectangle does not fit, or asks for more cells than it holds.
            Neither is loud in SQX: a rectangle that does not fit falls back to the single
            best cell and counts it as one (`findBestGroupOfPassedCombinations`, decompiled
            2026-09-24), so every strategy is dismissed and nothing says why.
    """
    if size > min(rows, cols):
        raise SystemExit(f"un area de {size}x{size} no cabe en una matriz de {rows}x{cols}. "
                         "SQX no avisa: se queda con la mejor casilla suelta y la cuenta "
                         "como una, asi que descartaria todo.")
    if minimum > size * size:
        raise SystemExit(f"min_squares {minimum} es imposible en un area de {size}x{size}: "
                         f"solo tiene {size * size} casillas.")
    return {"thresholdPct": threshold_pct, "robCombRows": size, "robCombCols": size,
            "robMinComb": minimum}


def acceptance(block: str, specs: list[dict], attrs: dict[str, int], crosscheck: str) -> str:
    """Replace a cross-check's whole `<Conditions>` element -- its attributes and its list.

    Args:
        block: The cross-check element, e.g. `<WalkForwardMatrix>...</WalkForwardMatrix>`.
        specs: The conditions to write, as `condition` reads them.
        attrs: The element's own attributes, e.g. `thresholdPct` and, on the matrix, the
            three that describe the area (`robCombRows`, `robCombCols`, `robMinComb`).
        crosscheck: Element name, passed through to every condition's `resultType`.

    Returns:
        The element with the old conditions gone and these in their place. Replacing rather
        than appending is the point: what a donor task carries is someone else's judgement,
        and a leftover condition counts in the score exactly like one that was chosen.
    """
    written = "".join(condition(spec, crosscheck) for spec in specs)
    attributes = " ".join(f'{name}="{value}"' for name, value in attrs.items())
    found = CONDITIONS.search(block)
    return (block[:found.start()] + f"<Conditions {attributes}>{written}</Conditions>"
            + block[found.end():])
