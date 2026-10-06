"""Level 2 of the gate: what the edge keeps when entry, exit or both slip one bar."""

import numpy as np
import pandas as pd

from studies.screening.analysis import delay

FACTS = ("retraso_ret_min", "retraso_t_delta")


def run(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """The one-bar delay for the strategies alive, judged on the variant that keeps least.

    Args:
        data: The harvest as `inputs.load` gives it, plus `bars`, `market`, `costs`, `out` and
            `oos`, level 1a's per-trade table of oos1; with `delay.on_build` also
            `costs_build`, reprice.costs of the feed's build segment.
        alive: Identities still in the cascade.
        cfg: The gate's config; reads `delay` and `drift`.

    Returns:
        Indexed by `alive`: `retraso_ret_min`, the smallest of the variants' mean moved excess
        over mean original excess, and `retraso_t_delta`, the paired t of original minus moved
        of that same variant; both empty when the original mean excess is not positive. It
        also writes every variant's row into `out` as `retraso.parquet` (delay.measure) and,
        with `delay.on_build`, the build's as `retraso_build.parquet`, which no fact reads.
    """
    if not data:       # tests/test_gate_rules.py runs every level on an empty harvest
        return pd.DataFrame(index=alive, columns=list(FACTS), dtype=float)
    bars, windows, drift = data["bars"], data["market"]["windows"], cfg["drift"]
    variants = cfg["delay"]["variants"]
    oos = data["oos"][data["oos"]["identity"].isin(alive)]
    table = delay.measure(oos, bars, windows["OOS"], data["costs"], drift, variants)
    table.to_parquet(data["out"] / "retraso.parquet", index=False)
    if cfg["delay"]["on_build"]:
        raw = data["trades"]
        raw = raw[(raw["sample"] == "IS") & raw["identity"].isin(alive)]
        raw = raw.sort_values(["identity", "Close time"])
        build = pd.DataFrame({
            "identity": raw["identity"].to_numpy(), "open_time": raw["Open time"].to_numpy(),
            "close_time": raw["Close time"].to_numpy(), "lots": raw["Size"].to_numpy(),
            "side": np.where(raw["Type"].astype(str) == "Sell", -1.0, 1.0)})
        build["excess"] = delay.excess(build, bars, windows["IS"], data["costs_build"], drift)
        delay.measure(build, bars, windows["IS"], data["costs_build"], drift, variants) \
            .to_parquet(data["out"] / "retraso_build.parquet", index=False)
    return (delay.worst(table)[["ret", "t_delta"]].set_axis(list(FACTS), axis=1)
            .reindex(alive))
