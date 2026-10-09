"""Exact duplicates among a batch's variants, told by the trades they made and not by a total."""

import hashlib
from collections.abc import Sequence

import numpy as np
import pandas as pd

COLUMNS = ("Open time", "Close time", "Type", "Size", "Open price", "Close price", "Profit/Loss")


def prints(trades: pd.DataFrame, unit: str = "variant_id",
           columns: Sequence[str] = COLUMNS) -> pd.Series:
    """One hash per variant of its whole trade list.

    Args:
        trades: Every trade of the variants compared, the same legs and markets for all.
        unit: The column naming the variant.
        columns: What makes two trades the same one; compared exactly, as exported.

    Returns:
        Indexed by variant, a hex digest of its trades in time order. Two variants share it
        only when every trade matches; a variant without a trade has no row.
    """
    rows = trades.sort_values([unit, *columns], kind="stable")
    row = pd.util.hash_pandas_object(rows[list(columns)], index=False)
    return row.groupby(rows[unit].to_numpy(), sort=False).agg(
        lambda h: hashlib.blake2b(h.to_numpy(np.uint64).tobytes(), digest_size=16).hexdigest())


def keep(fingerprint: pd.Series, first: Sequence = ()) -> tuple[pd.Index, float]:
    """The variants left when every set of identical trade lists is cut to one.

    Args:
        fingerprint: What prints() returned.
        first: Variants that win their set, the mother before any copy of her.

    Returns:
        (the variants kept, in `fingerprint`'s order: of each fingerprint one of `first`, else
        the earliest; the share of variants dropped as duplicates).
    """
    front = fingerprint.index.isin(first)
    kept = ~fingerprint.iloc[np.argsort(~front, kind="stable")].duplicated().reindex(fingerprint.index)
    return fingerprint.index[kept.to_numpy()], float(1 - kept.mean())
