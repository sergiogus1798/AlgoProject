"""The diverse shortlist: the best combinations of a search, no two sharing more than a set share of members."""

import pandas as pd

OF = {"smaller": min, "larger": max}


def ranked(search: pd.DataFrame) -> pd.DataFrame:
    """A search's distinct combinations, best first.

    Args:
        search: `search.parquet` — `members` (identities joined with "+"), `score`, `level`.

    Returns:
        One row per distinct member set with a finite score, sorted by score (the search's
        own order breaks ties): `members`, `score`, `level`.
    """
    best = search.dropna(subset=["score"]).sort_values("score", ascending=False, kind="stable")
    return best.drop_duplicates("members")[["members", "score", "level"]].reset_index(drop=True)


def diverse(ranking: pd.DataFrame, size: int, max_shared: float, shared_of: str) -> pd.DataFrame:
    """Walk the ranking, keeping a combination unless it is too close to one already kept.

    Args:
        ranking: `ranked()` output.
        size: Combinations to keep at most.
        max_shared: Two combinations are too close when they share **more** than this share
            of their members (0.5: more than half).
        shared_of: Whose members when the two differ in size: "smaller" or "larger".

    Returns:
        The kept rows, in ranking order, with `rank` (their place in the full ranking).
    """
    base = OF[shared_of]
    kept, sets = [], []
    for rank, members in enumerate(ranking["members"]):
        own = set(members.split("+"))
        if all(len(own & other) <= max_shared * base(len(own), len(other)) for other in sets):
            kept.append(rank)
            sets.append(own)
            if len(kept) == size:
                break
    return ranking.iloc[kept].assign(rank=kept).reset_index(drop=True)
