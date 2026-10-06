"""Level 1b of the gate, the facts centred on the population: frequency stability and decay inside oos1."""

import numpy as np
import pandas as pd

from studies.screening.analysis import centred

FACTS = ("z_frec", "t_b", "e_fin")


def run(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """R5 and R5d, each against the centre of the run's strategies of the same side.

    Args:
        data: The harvest as `inputs.load` gives it, plus `market` (inputs.market) and `oos`,
            the per-trade table of oos1 level 1a leaves, of every paired strategy.
        alive: Identities still in the cascade.
        cfg: The gate's config; reads `frequency` and `centring`.

    Returns:
        Indexed by `alive`. `z_frec`: the log of the ratio of trades per year, oos1 over build,
        minus its population's centre, over the Poisson error widened by the build's own
        yearly overdispersion. `t_b`: the slope of the excess against the close time inside
        oos1, minus its population's centre, over its standard error. `e_fin`: the strategy's
        own fitted excess at the end of oos1, uncentred. The centres are taken over every
        strategy in `oos`, fallen or not — one run is one asset and timeframe, so the
        population is the side.
    """
    if not data:       # tests/test_gate_rules.py runs every level on an empty harvest
        return pd.DataFrame(index=alive, columns=list(FACTS), dtype=float)
    oos, market, own = data["oos"], data["market"], cfg["centring"]
    by = oos.groupby("identity", sort=False)
    side = np.sign(by["side"].mean())
    build = data["trades"][data["trades"]["sample"] == "IS"]
    exposure = centred.calendar_exposure(*(pd.Timestamp(edge) for edge in market["windows"]["IS"]))
    counts = (pd.crosstab(build["identity"], build["Open time"].dt.year)
              .reindex(index=side.index, columns=exposure.index, fill_value=0))
    phi = centred.dispersion(counts, exposure, cfg["frequency"]["phi_min"],
                             cfg["frequency"]["phi_max"])
    rate = centred.rate_change(counts.sum(axis=1), market["years"]["IS"], by.size(),
                               market["years"]["OOS"], phi)
    end = pd.Timestamp(market["windows"]["OOS"][1])
    fit = centred.slope(oos, "excess", (oos["close_time"] - end) / pd.Timedelta(days=centred.YEAR))
    middle = {"log_rate": centred.centre(rate["log_rate"], side, own["min_strategies"],
                                         own["cap_log_rate"]),
              "b": centred.centre(fit["b"], side, own["min_strategies"], own["cap_slope"])}
    return pd.DataFrame({"z_frec": (rate["log_rate"] - middle["log_rate"]) / rate["se"],
                         "t_b": (fit["b"] - middle["b"]) / fit["se"],
                         "e_fin": fit["at_zero"]}).reindex(alive)
