"""Level 1b of the gate, the facts centred on the population: frequency stability and decay inside oos1."""

import pandas as pd

from studies.screening.analysis import centred

FACTS = ("z_frec", "t_b", "e_fin")


def run(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """R5 and R5d, each against the centre of the run's strategies of the same side.

    A strategy that trades both sides belongs to neither: those form a population of their own.

    Args:
        data: The harvest as `inputs.load` gives it, plus `market` (inputs.market) and `oos`,
            the per-trade table of oos1 level 1a leaves, of every paired strategy.
        alive: Identities still in the cascade.
        cfg: The gate's config; reads `frequency` and `centring`.

    Returns:
        Indexed by every strategy in `oos`, fallen or not, and by `alive` (wider than `alive`:
        the centre needs everyone, and everyone keeps its facts). `z_frec`: the log of the ratio of trades per year, oos1 over build,
        minus its population's centre, over the Poisson error widened by the build's own
        yearly overdispersion. `t_b`: the slope of the excess against the close time inside
        oos1, minus its population's centre, over its standard error. `e_fin`: the mean excess
        plus that centred slope x half the years of oos1 — where the excess ends once the
        population's common slope is taken out. One run is one asset and timeframe, so the
        population is the side.
    """
    if not data:       # tests/test_gate_rules.py runs every level on an empty harvest
        return pd.DataFrame(index=alive, columns=list(FACTS), dtype=float)
    oos, market, own = data["oos"], data["market"], cfg["centring"]
    by = oos.groupby("identity", sort=False)
    side = by["side"].min().where(by["side"].min() == by["side"].max(), 0.0)   # 0 = both
    build = data["trades"][data["trades"]["sample"] == "IS"]
    exposure = centred.calendar_exposure(*(pd.Timestamp(edge) for edge in market["windows"]["IS"]))
    counts = (pd.crosstab(build["identity"], build["Open time"].dt.year)
              .reindex(index=side.index, columns=exposure.index, fill_value=0))
    phi = centred.dispersion(counts, exposure, cfg["frequency"]["phi_min"],
                             cfg["frequency"]["phi_max"])
    rate = centred.rate_change(counts.sum(axis=1), market["years"]["IS"], by.size(),
                               market["years"]["OOS"], phi)
    fit = centred.slope(oos, "excess", (oos["close_time"] - oos["close_time"].min())
                        / pd.Timedelta(days=centred.YEAR))
    middle = {"log_rate": centred.centre(rate["log_rate"], side, own["min_strategies"],
                                         own["cap_log_rate"]),
              "b": centred.centre(fit["b"], side, own["min_strategies"], own["cap_slope"])}
    b = fit["b"] - middle["b"]
    return pd.DataFrame({"z_frec": (rate["log_rate"] - middle["log_rate"]) / rate["se"],
                         "t_b": b / fit["se"],
                         "e_fin": fit["mean"] + b * market["years"]["OOS"] / 2},
                        columns=list(FACTS)).reindex(side.index.union(alive, sort=False))
