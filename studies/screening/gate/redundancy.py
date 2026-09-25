"""The soft screen: are these N strategies, or one strategy repeated N times?"""

import pandas as pd


def redundancia(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """Group the survivors by the logic they are, ignoring what their parameters say.

    Args:
        data: What inputs.load returned.
        alive: Strategies still in the cascade.
        cfg: This screen's row of config.yaml.

    Returns:
        `value` is how many strategies share each one's structure, and `note` names the
        group's first member and its size.

        The grouping is the `structure` column of the harvest: the ordered block keys of
        `strategy_Portfolio.xml`, with parameter VALUES dropped. Two strategies share it
        when they are the same rules at different settings — a period of 14 and one of 90
        are one idea, not two. 🔬 2026-09-23: 115 survivors of a sample build were 24
        structures, two of which held 32 strategies each.

        This replaced grouping by the correlation of daily returns (owner, 2026-09-23).
        Correlation is a proxy and it is window-dependent: two unrelated strategies that
        happened to be long through the same rally correlate, and the same logic at two
        parameter settings may not. The XML is what the strategy IS, and reading it costs
        0.2 ms.

        **Nobody is eliminated.** Two strategies built on one shape are still two bets
        with different parameters, and dropping one here would throw away a real one to
        tidy the list. What this buys is knowing that "40 survivors" may be 6 distinct
        ideas before a portfolio is built on them.
    """
    shape = data["metrics"].loc[alive, "structure"]
    size = shape.map(shape.value_counts())
    first = shape.map(data["metrics"].loc[alive].groupby("structure")["strategy"].first())
    note = first.where(size == 1, "grupo de " + first + " (" + size.astype(str) + ")")
    return pd.DataFrame({"value": size, "passed": True,
                         "note": note.mask(size == 1, "única")}).reindex(alive)
