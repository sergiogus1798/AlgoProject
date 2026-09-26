"""One feed's anomalies under a given K and session: spikes on close and wick, frozen runs, gaps."""

import numpy as np
import pandas as pd

from engines.market.feed import runs, scale, session, spikes

COLUMNS = ["kind", "cls", "start_min", "end_min", "size", "rev_m1", "rev_m5", "both"]
ROLLOVER = "rollover"


def measure(b: dict, tick: float, cfg: dict) -> dict:
    """Each bar's scale and its move on the close and on the wick in multiples of it.

    Args:
        b: inputs.bars()'s dict.
        tick: The feed's price increment.
        cfg: inputs.config()'s dict.

    Returns:
        {"r", "sigma", "raw" (sigma before its floors), "z_close", "z_wick", "reach_close",
        "reach_wick"} per bar. The reach is the jump from the previous close each column's
        reversion is measured against.
    """
    s = cfg["scale"]
    r = scale.returns(b["c"], b["at"])
    cells, first = scale.by_week(r, b["at"], s["window_weeks"], s["min_weeks"])
    sigma = scale.sigma(b["c"], b["at"], cells, first, tick, s["floor_ticks"], s["floor_rel"])
    got = spikes.spikes(b["o"], b["h"], b["l"], b["c"], b["at"], r, sigma)
    prev = np.r_[b["c"][0], b["c"][:-1]]
    return {"r": r, "sigma": sigma, "raw": scale.own(b["at"], cells, first),
            "z_close": got["z_close"], "z_wick": got["z_wick"],
            "reach_close": np.nan_to_num(np.abs(r)),
            "reach_wick": np.abs(np.log(got["wick_price"] / prev))}


def _spikes(b: dict, got: dict, column: str, k: float, cfg: dict) -> pd.DataFrame:
    """One column's bars over K, classified by their return at m and at the sensitivity m's."""
    sp = cfg["spike"]
    z, reach = got[f"z_{column}"], got[f"reach_{column}"]
    i, back = spikes.classify(b["c"], b["at"], z, reach, k, sp["m"], sp["rho"])
    other = got["z_wick" if column == "close" else "z_close"]
    m1, m5 = (spikes.reverted(b["c"], b["at"], i, reach[i], m, sp["rho"])
              & (b["at"][i] - b["at"][i - 1] == 1) for m in sp["m_sensitivity"])
    return pd.DataFrame({"kind": "cierre" if column == "close" else "mecha",
                         "cls": np.where(back, "vuelta", "extremo"),
                         "start_min": b["at"][i], "end_min": b["at"][i] + 1, "size": z[i],
                         "rev_m1": m1, "rev_m5": m5, "both": other[i] >= k})


def _runs(b: dict, band: np.ndarray, cls: str, cfg: dict) -> pd.DataFrame:
    """Frozen runs inside one band of the week."""
    at = b["at"]
    fr = runs.frozen(b["o"], b["h"], b["l"], b["c"], at, band[at % scale.WEEK],
                     cfg["frozen"]["length"])
    return pd.DataFrame({"kind": "congelado", "cls": cls, "start_min": at[fr["start"]],
                         "end_min": at[fr["start"]] + fr["bars"], "size": fr["bars"]})


def _holes(at: np.ndarray, band: np.ndarray, cls: str, cfg: dict) -> pd.DataFrame:
    """Gaps counted in the minutes of one band of the week."""
    gp = runs.gaps(at, band, cfg["gap"]["minutes"])
    return pd.DataFrame({"kind": "hueco", "cls": cls, "start_min": gp["from_min"],
                         "end_min": gp["to_min"], "size": gp["minutes"]})


def events(b: dict, got: dict, k: float, week_mask: np.ndarray, cfg: dict) -> pd.DataFrame:
    """Every anomaly of one feed, one row each.

    Args:
        b: inputs.bars()'s dict.
        got: measure()'s dict.
        k: The feed's K.
        week_mask: The feed's session.
        cfg: inputs.config()'s dict.

    Returns:
        COLUMNS plus `t`, the anomaly's first minute. Spikes last one minute; a frozen run
        its bars; a gap its missing span, `size` counting only its in-session minutes. Frozen
        runs and gaps inside the rollover hours are `cls` "rollover": counted, never marked
        (owner, 2026-09-26). The other gaps are all "símbolo" here: calendar.classify()
        tells the shared silences apart.
    """
    at = b["at"]
    counted = session.without_hours(week_mask, cfg["rollover_hours"])
    rollover = week_mask & ~counted
    frozen = pd.concat([_runs(b, band, cls, cfg) for band, cls in
                        ((counted, "congelado"), (rollover, ROLLOVER))], ignore_index=True)
    holes = pd.concat([_holes(at, band, cls, cfg) for band, cls in
                       ((counted, "símbolo"), (rollover, ROLLOVER))], ignore_index=True)
    out = pd.concat([_spikes(b, got, "close", k, cfg), _spikes(b, got, "wick", k, cfg),
                     frozen, holes], ignore_index=True)[COLUMNS]
    out["t"] = pd.to_datetime((out["start_min"] + scale.ORIGIN) * scale.MINUTE_NS)
    return out.sort_values(["start_min", "kind"], ignore_index=True)


def yearly_counts(b: dict, got: dict, ks: list[int]) -> pd.DataFrame:
    """Close spikes per calendar year at each candidate K, the table K* is chosen from.

    Args:
        b: inputs.bars()'s dict.
        got: measure()'s dict.
        ks: Candidate K values.

    Returns:
        Years as rows, one column per K.
    """
    year = b["t"].year
    return pd.DataFrame({k: pd.Series(got["z_close"] >= k).groupby(year).sum() for k in ks})
