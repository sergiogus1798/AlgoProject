"""P2: the frequency of each strategy in each market against its own on the main asset, centred on what the population does there."""

from typing import cast

import pandas as pd

from studies.screening.analysis import centred


def z_freq(counts: pd.DataFrame, years: pd.Series, main: pd.DataFrame, cuts: dict,
           frequency: dict) -> pd.DataFrame:
    """z_freq of §2.4 b for every strategy and market.

    Args:
        counts: Trades per strategy (rows) and market (columns), the export's, whole own window.
        years: Length of each market's own window, years, indexed like the columns.
        main: The main asset's trades over build + oos1, one row each: `strategy` and
            `Open time`. The overdispersion is estimated on those opened before oos1.
        cuts: `cells.cuts(asset)`; its build..end is the main's window.
        frequency: travel.frequency (`phi_min`, `phi_max`).

    Returns:
        (strategies, markets) of z = (ln(r_j / r_main) - m_pop,j) / sqrt(phi (1/N_j + 1/N_main)),
        m_pop,j the median over the export's strategies (`centred.centre`; a lone strategy is
        not a population, its centre is 0). NaN where the strategy has no trade in the market or
        none on the main: no data is not a z of 0.
    """
    exposure = centred.calendar_exposure(cuts["build"], cuts["oos1"])
    build = main[main["Open time"] < cuts["oos1"]]
    by_year = pd.crosstab(build["strategy"], cast(pd.Series, build["Open time"]).dt.year).reindex(
        index=counts.index, columns=exposure.index, fill_value=0)
    phi = centred.dispersion(by_year, exposure, frequency["phi_min"], frequency["phi_max"])
    n_main = cast(pd.Series, main.groupby("strategy").size().reindex(counts.index, fill_value=0))
    span = (cuts["end"] - cuts["build"]) / pd.Timedelta(days=centred.YEAR)
    group = pd.Series("population", index=counts.index)
    out = {}
    for feed in counts.columns:
        rate = centred.rate_change(n_main, span, cast(pd.Series, counts[feed]), cast(float, years[feed]), phi)
        out[feed] = (rate["log_rate"] - centred.centre(cast(pd.Series, rate["log_rate"]), group, 2, None)) / rate["se"]
    return pd.DataFrame(out)
