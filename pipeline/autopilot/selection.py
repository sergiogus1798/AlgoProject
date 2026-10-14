"""Who a judging step keeps and drops: the identity lookup, the fallen, the medoid cut and the siblings."""

import sys
from collections.abc import Mapping
from typing import cast

import pandas as pd

from pipeline.autopilot import facts
from sqx.projects.crosstfload import SIBLING


def resolve(pop: pd.DataFrame, found: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """The key each file of the cut databank and each fact is judged under: the one lookup.

    Args:
        pop: The databank being cut: `strategy` (file name) and `identity`, one row per file.
        found: The facts: `strategy` and `identity` ("" when a study files by name only).

    Returns:
        (`who` of every row of `pop`, `who` of every row of `found`). A file is its identity
        when any fact carries it, else its name; a fact is its identity, or its strategy name
        when it has none. A fact filed under an identity the cut databank does NOT hold — the
        gate, spread and edgeCost key by the BUILD's, which a retest can change (🔬 2026-10-06:
        1,557 of 10,000 failed presence for it, 29 of them alive on their own numbers) — is the
        file of the same name: a name is unique inside one databank. A fact without identity
        keeps its key, so nothing moves for a strategy whose identity held.
    """
    ids = set(found["identity"]) - {""}
    who = pd.Series(
        [i if i in ids else s for s, i in zip(pop["strategy"], pop["identity"])],
        index=pop.index,
        dtype=object,
    )
    theirs = found["identity"].where(found["identity"] != "", found["strategy"])
    named = cast(pd.Series, found["strategy"]).map(
        cast("Mapping[str, str]", dict(zip(pop["strategy"], who)))
    )
    held = found["identity"].isin(list(set(pop["identity"]) | {""}))
    return who, cast(pd.Series, theirs.where(held | named.isna(), named))


def fallen(project: str, pop: pd.DataFrame) -> dict[str, str]:
    """Why the gate's cascade dropped each strategy it dropped: `who` → its first failed rule.

    The gate stops computing at a strategy's first Fail, so every rule of a later level reads
    «sin dato» for it: the reason is the one rule the scorecard names (`cayo_nivel`,
    `cayo_regla`), which is text and so not among the facts.
    """
    found = [
        r for r in facts.sources.results(project, "gate", None) if r["path"].is_dir()
    ]
    if not found:
        return {}
    card = pd.read_parquet(found[0]["path"] / "scorecard.parquet").reset_index()
    if "cayo_regla" not in card:  # a scorecard written before the gate ran by levels
        return {}
    card = cast(
        pd.DataFrame, card[card["strategy"].notna() & card["cayo_regla"].notna()]
    )
    _, who = resolve(pop, card)
    return {
        w: f"fail: {rule} (nivel {level})"
        for w, level, rule in zip(who, card["cayo_nivel"], card["cayo_regla"])
    }


def largest(card: pd.DataFrame, top: int) -> pd.DataFrame:
    """The scorecard rows of the medoids of the `top` largest groups: size (`redundancia_value`,
    counted among the same survivors) descending, tie by `redundancia_grupo` ascending."""
    mine = cast(pd.DataFrame, card[card["medoide"].fillna(False).astype(bool)])
    return cast(
        pd.DataFrame,
        mine.sort_values(
            ["redundancia_value", "redundancia_grupo"], ascending=[False, True]
        ).head(top),
    )


def medoids(project: str, pop: pd.DataFrame, top: int) -> set[str]:
    """`who` of the medoids of the `top` largest groups the gate marked in its scorecard."""
    found = [
        r for r in facts.sources.results(project, "gate", None) if r["path"].is_dir()
    ]
    card = (
        pd.read_parquet(found[0]["path"] / "scorecard.parquet").reset_index()
        if found
        else None
    )
    if card is None or "medoide" not in card:
        sys.exit(
            "paso con `medoids`: el scorecard de la puerta no trae la columna `medoide`"
        )
    _, who = resolve(
        pop, largest(cast(pd.DataFrame, card[card["strategy"].notna()]), top)
    )
    return set(who)


def siblings(
    pop: pd.DataFrame,
    is_sibling: pd.Series,
    judged: dict[str, tuple[str, str]],
    follow: bool,
) -> dict[str, tuple[str, str]]:
    """What happens to the scaled siblings of the databank being cut.

    Args:
        pop: The databank being cut, with `strategy` and `who`.
        is_sibling: Which rows of `pop` are scaled siblings.
        judged: The mothers' outcomes, `who` → (state, why).
        follow: `siblings: follow` in the step's criteria — step 11.5, whose databank feeds
            11.7 and still needs them: a sibling leaves only with its mother. Otherwise (step
            12, as always) every sibling goes: only the mother is a candidate.

    Returns:
        `who` of every sibling → (state, why).
    """
    mine = pop[is_sibling]
    if not follow:
        return {
            w: ("fail", "hermana escalada: solo sigue la madre") for w in mine["who"]
        }
    by_name = dict(zip(pop["strategy"], pop["who"]))
    return {
        w: judged.get(
            cast(str, by_name.get(SIBLING.sub("", name))),
            ("fail", "hermana sin su madre en el databank"),
        )
        for name, w in zip(mine["strategy"], mine["who"])
    }
