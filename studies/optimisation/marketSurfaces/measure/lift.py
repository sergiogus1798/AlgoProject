"""The criteria metrics of the surfaces: the Jaccard's lift over a zero-edge market, and the mother in each market's top."""

import numpy as np

LEVELS = (5, 25, 50, 75, 95)
DRAWS = 1000
SEED = 17
MIN_VARIANTS = 10      # below this a market's top share is one variant: no reading, not a zero


def tops(nets: np.ndarray, k: int) -> np.ndarray:
    """Which variants are in the best `k` of each row; ties at the cut broken by position."""
    order = np.argsort(-nets, axis=1, kind="stable")[:, :k]
    out = np.zeros(nets.shape, dtype=bool)
    np.put_along_axis(out, order, True, axis=1)
    return out


def flipped(days: np.ndarray, signs: np.ndarray, k: int) -> np.ndarray:
    """The top-k of one market's surface under zero edge, one row per draw.

    Each day's profit keeps its size and takes a random sign, the same for every variant:
    every variant expects zero, and the variants stay as alike as their trades made them —
    which is what makes a top of neighbours overlap another by chance more than the
    hypergeometric of independent variants says.

    Args:
        days: Daily profit of the market in the segment, days down, variants across.
        signs: ±1, draws down, the same days across.
        k: Size of the top set.
    """
    return tops(signs @ days, k)


def jaccard(x: np.ndarray, k: int) -> np.ndarray:
    """J of two top-k sets that share `x` members."""
    return x / (2 * k - x)


def market(main_top: np.ndarray, own_top: np.ndarray, null: np.ndarray, origin: int | None) -> dict:
    """One secondary market against the main one.

    Args:
        main_top: Variants in the main market's top share (its real surface: the null moves
            the other market only).
        own_top: Variants in this market's top share.
        null: `flipped` for this market.
        origin: The mother's position, None when it is not among the variants both keep.

    Returns:
        `j`; `chance` — the mean J over the zero-edge draws; `lift` = j / chance; `lifts` —
        every draw's J over that same mean (its expectation is 1 by construction); `inside`
        — whether the mother is in this market's top; `inside_null` — the same per draw.
    """
    k = int(main_top.sum())
    js = jaccard((null & main_top).sum(axis=1), k)
    chance = float(js.mean())
    return {"j": float(jaccard((main_top & own_top).sum(), k)), "chance": chance,
            "lift": float(jaccard((main_top & own_top).sum(), k) / chance) if chance else None,
            "lifts": js / chance if chance else None,
            "inside": None if origin is None else bool(own_top[origin]),
            "inside_null": None if origin is None else null[:, origin]}


def together(markets: dict[str, dict]) -> dict:
    """What a segment's secondary markets say as one: the median lift and the mother's share.

    Args:
        markets: Market → `market`, only those with a reading. The draws are shared (one
            sign per calendar day for every market), so the markets move together under
            the null as they do in the data.

    Returns:
        `lift` — the median over markets; `inside` — the share of markets whose top holds
        the mother; `baseline` — that share under zero edge; `excess` = inside − baseline;
        `null` — the `LEVELS` percentiles of the median lift and of the excess over draws.
        None where no market offers the number.
    """
    lifts = [m for m in markets.values() if m["lift"] is not None]
    held = [m for m in markets.values() if m["inside"] is not None]
    out = {"lift": None, "inside": None, "baseline": None, "excess": None, "markets": len(lifts),
           "null": {"lift": None, "excess": None}}
    if lifts:
        out["lift"] = float(np.median([m["lift"] for m in lifts]))
        out["null"]["lift"] = [float(v) for v in np.percentile(
            np.median([m["lifts"] for m in lifts], axis=0), LEVELS)]
    if held:
        share = np.mean([m["inside_null"] for m in held], axis=0)
        out |= {"inside": float(np.mean([m["inside"] for m in held])),
                "baseline": float(share.mean())}
        out["excess"] = out["inside"] - out["baseline"]
        out["null"]["excess"] = [float(v) for v in np.percentile(share - share.mean(), LEVELS)]
    return out
