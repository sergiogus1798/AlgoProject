"""What each scaled cell means, once the control and the rounding have had their say."""

import pandas as pd

# The five readings, in the order the checks are applied. Each names what it blames, which
# is the whole point of having the control cell: "it died on H4" and "it died when its
# periods changed" are different findings and only one of them is about timeframes.
MEANS = {
    "unusable": "rounding or clamping moved the parameters too far to attribute anything",
    "silent": "the entry never fired on that timeframe, so there is nothing to judge",
    "control_failed": "the parameter change alone broke it on its own timeframe",
    "survives": "beats its own timeframe's entry-timing null",
    "inherited": "profitable on the new timeframe, but not distinguishable from chance on it",
    "fails": "does not carry over",
}


def usable(row: pd.Series, scaling: pd.DataFrame, cfg: dict) -> bool:
    """Whether a scaled cell's parameters survived the rescaling well enough to be read.

    Args:
        row: One `scaled` cell of the panel.
        scaling: The manifest `sqx.variants.scale` wrote.
        cfg: The `usable` section of the study's config.

    Returns:
        False when a period was clamped at the builder's floor or when rounding moved one
        further than the study's tolerance -- either way the cell is measuring the
        parameter change as much as the timeframe.
    """
    made = scaling[scaling["name"] == row["strategy"]].iloc[0]
    return not (cfg["reject_clamped"] and made["clamped"]) \
        and made["max_rounding_shift"] <= cfg["max_rounding_shift"]


def read(panel: pd.DataFrame, scaling: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """One reading per scaled cell, with the two cells it was judged against.

    Args:
        panel: What `cells.panel` returned.
        scaling: The manifest `sqx.variants.scale` wrote.
        cfg: What `inputs.config` returned.

    Returns:
        One row per scaled cell: its mother, timeframe, statistic, p, the baseline and
        control it was compared with, and `reading`, a key of `MEANS`.

    The control is read before the p on purpose, and `silent` before both: the order of
    the checks is the order of the blame.
    """
    alpha, drop = cfg["verdict"]["alpha"], cfg["verdict"]["control_drop"]
    base = panel[panel["role"] == "baseline"].set_index("mother")["seen"]
    control = panel[panel["role"] == "control"].set_index("strategy")["seen"]

    rows = []
    for _, cell in panel[panel["role"] == "scaled"].iterrows():
        baseline, ctrl = base[cell["mother"]], control[cell["strategy"]]
        if not usable(cell, scaling, cfg["usable"]):
            reading = "unusable"
        # A cell with no trades is not a failure: a strategy that never entered has not
        # lost money there, and grading it as `fails` would count silence as evidence.
        elif cell["trades"] == 0:
            reading = "silent"
        elif ctrl < baseline * (1 - drop):
            reading = "control_failed"
        elif cell["p"] < alpha:
            reading = "survives"
        elif cell["seen"] > 0:
            reading = "inherited"
        else:
            reading = "fails"
        rows.append({"mother": cell["mother"], "timeframe": cell["timeframe"],
                     "seen": cell["seen"], "p": cell["p"], "trades": cell["trades"],
                     "baseline": baseline, "control": ctrl, "reading": reading,
                     "warnings": cell["warnings"]})
    return pd.DataFrame(rows)


def unscaled(panel: pd.DataFrame) -> pd.DataFrame:
    """The mother's own row, which answers a different question and carries no verdict.

    Whether the mother is also profitable on H4 or D1 with its periods left alone is a
    question about the market's self-similarity, not about the strategy being overfit.
    Failing it is not evidence against the strategy, so nothing here is graded.

    Args:
        panel: What `cells.panel` returned.

    Returns:
        The baseline and unscaled cells, with their statistic, p and trade count.
    """
    rows = panel[panel["role"].isin(["baseline", "unscaled"])]
    return rows[["mother", "timeframe", "role", "trades", "seen", "p"]].reset_index(drop=True)


def counts(readings: pd.DataFrame) -> dict:
    """How the population fell across the five readings, per timeframe.

    Args:
        readings: What `read` returned.

    Returns:
        Timeframe to reading to count.
    """
    table = readings.pivot_table(index="timeframe", columns="reading", values="mother",
                                aggfunc="count", observed=True).fillna(0).astype(int)
    return {tf: dict(row) for tf, row in table.iterrows()}
