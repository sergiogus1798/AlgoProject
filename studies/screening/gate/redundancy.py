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
    if not len(alive):  # nobody standing: nothing to group
        return pd.DataFrame(columns=pd.Index(["value", "passed", "note"]))
    shape = data["metrics"].loc[alive, "structure"]
    size = shape.map(shape.value_counts())
    first = shape.map(
        data["metrics"].loc[alive].groupby("structure")["strategy"].first()
    )
    note = first.where(size == 1, "grupo de " + first + " (" + size.astype(str) + ")")
    return pd.DataFrame(
        {"value": size, "passed": True, "note": note.mask(size == 1, "única")}
    ).reindex(alive)


def medoides(metrics: pd.DataFrame, oos: pd.DataFrame, alive: pd.Index) -> pd.DataFrame:
    """The medoid of every structure group among the survivors.

    Args:
        metrics: The harvest's metrics, indexed by identity: `structure` and `strategy` (name).
        oos: Per-trade table with `identity` and `open_time` (the gate's `operaciones.parquet`).
        alive: Identities standing.

    Returns:
        Indexed by `alive`: `grupo` (the group's first name) and `medoide` (bool). The medoid is
        the member with the highest mean Jaccard similarity of its set of entry bars against the
        others of its group (tie: name order; a group of one is its own medoid).
    """
    out = pd.DataFrame({"grupo": None, "medoide": False}, index=alive)
    if not len(alive):
        return out
    names = metrics.loc[alive, "strategy"]
    groups = {
        s: sorted(g.index, key=names.get)
        for s, g in metrics.loc[alive].groupby("structure")
    }
    out["grupo"] = [names[groups[metrics.at[i, "structure"]][0]] for i in alive]
    bars = {
        i: set(g)
        for i, g in oos[oos["identity"].isin(list(alive))].groupby("identity")[
            "open_time"
        ]
    }

    def jaccard(a: str, b: str) -> float:
        """Share of entry bars the two strategies have in common."""
        union = (
            len(bars.get(a, ()))
            + len(bars.get(b, ()))
            - len(bars.get(a, set()) & bars.get(b, set()))
        )
        return len(bars.get(a, set()) & bars.get(b, set())) / union if union else 0.0

    for members in groups.values():
        sim = {}  # symmetric: one Jaccard per unordered pair, summed in the same order as before
        for a, i in enumerate(members):
            for j in members[a + 1 :]:
                sim[i, j] = sim[j, i] = jaccard(i, j)
        score = {
            i: sum(sim[i, j] for j in members if j != i) / max(len(members) - 1, 1)
            for i in members
        }
        out.loc[
            members[max(range(len(members)), key=lambda a: (score[members[a]], -a))],
            "medoide",
        ] = True
    return out
