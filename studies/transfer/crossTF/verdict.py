"""What each scaled cell means on oos1, beyond what its mother's own result already explains."""

from statistics import NormalDist
from typing import cast

import pandas as pd

# ⚠️ AN AGENT'S PROPOSAL of 2026-10-02, pending the owner (README, «The reading»). The six
# readings, in the order the checks are applied. The first three say the test did not happen —
# a rule reads them as limbo, never as a failure.
MEANS = {
    "unusable": "carries a custom-block length nobody could rule on: it was not scaled",
    "silent": "the entry never fired on that timeframe in oos1, so there is nothing to judge",
    "no_data": "too few oos1 trades, on the sibling or on its mother, for a p",
    "survives": "beats its own timeframe's null in oos1, beyond what its mother explains",
    "inherited": "made money in oos1, but no more than its mother's result predicts",
    "fails": "lost money in oos1",
}


def usable(row: pd.Series, scaling: pd.DataFrame) -> bool:
    """Whether a scaled cell could be scaled at all.

    Args:
        row: One `scaled` cell of the panel.
        scaling: The manifest `sqx.variants.scale` wrote.

    Returns:
        False only when a custom block's length nobody could rule on was left unscaled
        (`sqx/variants/lengths.yaml`). Rounding and the floor no longer discard a sibling
        (owner, 2026-10-02: «Redondea donde puedas, ya está»): `rounding_shift` and
        `clamped` stay beside the reading as numbers, so a calibration can measure whether
        heavily rounded siblings behave differently, and nothing gates on them.
    """
    made = scaling[scaling["name"] == row["strategy"]].iloc[0]
    return not made.get("unverified", "")


def read(panel: pd.DataFrame, scaling: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """One reading per scaled cell, with the numbers it was read from.

    Args:
        panel: What `cells.panel` returned: every cell on its oos1 trades.
        scaling: The manifest `sqx.variants.scale` wrote.
        cfg: What `inputs.config` returned.

    Returns:
        One row per scaled cell: its mother, timeframe, trades, statistic, p, `z`, `z_new`,
        the baseline and the control beside it, and `reading`, a key of `MEANS`.

    `survives` asks for both: p under alpha against the cell's own null, and `z_new` over the
    same level's normal quantile -- a sibling of a lucky mother clears the first one 14-40 %
    of the time under no edge, the second one 5 %. The control (the sibling's parameters on
    the mother's bars) is shown and never read: it failed 29 of 46 real readings and
    inverted for a negative baseline.
    """
    alpha = cfg["verdict"]["alpha"]
    level = NormalDist().inv_cdf(1 - alpha)
    base = panel[panel["role"] == "baseline"].set_index("mother")["seen"]
    control = panel[panel["role"] == "control"].set_index("strategy")["seen"]

    rows = []
    for _, cell in panel[panel["role"] == "scaled"].iterrows():
        if not usable(cell, scaling):
            reading = "unusable"
        elif cell["trades"] == 0:
            reading = "silent"
        elif not cell["z_new"] == cell["z_new"]:
            reading = "no_data"
        elif cell["p"] < alpha and cell["z_new"] > level and cell["seen"] > 0:
            reading = "survives"
        elif cell["seen"] > 0:
            reading = "inherited"
        else:
            reading = "fails"
        rows.append(
            {
                "mother": cell["mother"],
                "timeframe": cell["timeframe"],
                "trades": cell["trades"],
                "seen": cell["seen"],
                "p": cell["p"],
                "z": cell["z"],
                "z_new": cell["z_new"],
                "baseline": base[cell["mother"]],
                "control": control[cell["strategy"]],
                "reading": reading,
                "warnings": cell["warnings"],
            }
        )
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
    return cast(
        pd.DataFrame, rows[["mother", "timeframe", "role", "trades", "seen", "p"]]
    ).reset_index(drop=True)


def counts(readings: pd.DataFrame) -> dict[str, dict[str, int]]:
    """How the population fell across the readings, per timeframe.

    Args:
        readings: What `read` returned.

    Returns:
        Timeframe to reading to count.
    """
    table = (
        readings.pivot_table(
            index="timeframe",
            columns="reading",
            values="mother",
            aggfunc="count",
            observed=True,
        )
        .fillna(0)
        .astype(int)
    )
    return {
        str(tf): {str(k): int(v) for k, v in row.items()}
        for tf, row in table.iterrows()
    }
