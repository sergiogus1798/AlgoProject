"""§2.2 — the point of no return: how many trades that went x ATR against still came back."""

import numpy as np
import pandas as pd

NOISE, NORETURN, THIN = "ruido", "sin retorno", "pocas operaciones"


def curve(trades: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """For each distance x, what became of the IS trades that reached it.

    Args:
        trades: The in-sample trades as `mae.measure` returned them, winners and losers.
        cfg: The study's config.

    Returns:
        One row per x: `reached` (trades whose MAE got to x), `recovered` (the share of them
        that ended winners), `mean_final` (their mean net result in ATR) and the `zone`:
        "sin retorno" when almost none recovered AND their mean final result is worse than
        -x — cutting there saves money and takes nothing — otherwise "ruido". It names the
        zone; it never picks an x.
    """
    knobs = cfg["noreturn"]
    xs = np.arange(knobs["x_step"], knobs["x_max"] + knobs["x_step"] / 2, knobs["x_step"])
    mae, won, final = (trades[c].to_numpy() for c in ("mae_atr", "winner", "result_atr"))
    rows = []
    for x in xs:
        hit = mae >= x
        n = int(hit.sum())
        recovered = float(won[hit].mean()) if n else np.nan
        mean_final = float(final[hit].mean()) if n else np.nan
        zone = (THIN if n < knobs["min_reached"] else
                NORETURN if recovered <= knobs["recover_max"] and mean_final < -x else NOISE)
        rows.append({"x": float(x), "reached": n, "recovered": recovered,
                     "mean_final": mean_final, "zone": zone})
    return pd.DataFrame(rows)


def zone_of(x: float, table: pd.DataFrame) -> str:
    """The zone the curve gives the step at or just below x.

    Args:
        x: One of the X, one per percentile.
        table: What `curve` returned.

    Returns:
        "ruido", "sin retorno" or "pocas operaciones". Below the first step, "ruido".
    """
    below = table[table["x"] <= x]
    return below["zone"].iloc[-1] if len(below) else NOISE
