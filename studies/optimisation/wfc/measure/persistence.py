"""The WFC's criteria metrics: persistence of the in-sample top, and the median OOS/IS ratio per variant."""

import numpy as np

LEVELS = (5, 25, 50, 75, 95)
DRAWS = 1000
SEED = 17


def persistence(inside: np.ndarray, outside: np.ndarray, top: float, keep: float) -> float:
    """Share of the in-sample top that stays in the out-of-sample top.

    Args:
        inside, outside: One value per variant on each side, same order (net profit).
        top: The in-sample top is this share of the variants (0.20: the best fifth).
        keep: «Stays» means inside this out-of-sample share (0.50: the upper half).

    Returns:
        Between 0 and 1. With no link between the two rankings it is `keep` in expectation:
        that baseline, not zero, is what the share is read against.
    """
    best = inside >= np.quantile(inside, 1.0 - top)
    return float((outside[best] >= np.quantile(outside, 1.0 - keep)).mean())


def ratio(inside: np.ndarray, outside: np.ndarray, floor: float) -> tuple[float | None, int]:
    """Median over variants of outside/inside — a median of ratios, not a ratio of medians.

    Args:
        inside, outside: One Sharpe per variant on each side, same order.
        floor: Only variants whose in-sample value is above this enter: a ratio over a
            denominator near zero or negative explodes or flips sign.

    Returns:
        (the median, how many variants entered); the median is None under five variants.
        Entering on a high in-sample value regresses to the mean by itself: a family with no
        decay at all reads somewhat below 1.
    """
    ok = inside > floor
    return (float(np.median(outside[ok] / inside[ok])) if ok.sum() >= 5 else None), int(ok.sum())


def flipped(days: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """The out-of-sample side of a zero-edge family: each day's sign drawn at random.

    Every variant's profit of a day is multiplied by the same ±1, so each variant's expected
    profit is zero while the variants stay exactly as dependent on each other as they are.

    Args:
        days: Daily profit, days down, variants across, the out-of-sample days only.
        rng: The generator.

    Returns:
        (net profit, annualised Sharpe — mean/sd·√252 of the daily profit), each `DRAWS`
        rows by one column per variant.
    """
    signs = rng.choice((-1.0, 1.0), (DRAWS, days.shape[0]))
    mean = signs @ days / days.shape[0]
    spread = np.sqrt(np.maximum((days ** 2).mean(axis=0) - mean ** 2, 0.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        return mean * days.shape[0], mean / spread * np.sqrt(252.0)


def measure(net_in: np.ndarray, net_out: np.ndarray, sharpe_in: np.ndarray, sharpe_out: np.ndarray,
            days: np.ndarray, top: float, keep: float, floor: float) -> dict:
    """Both metrics of one in-sample / out-of-sample pair, each beside its zero-edge null.

    Args:
        net_in, net_out: Net profit per usable variant, in and out of sample.
        sharpe_in, sharpe_out: SQX's annualised Sharpe per usable variant (NaN where absent).
        days: The same variants' daily profit over the out-of-sample days, for `flipped`.
        top, keep: `persistence`'s two shares.
        floor: `ratio`'s in-sample floor.

    Returns:
        `share`, `baseline` (= keep), `excess` (share − baseline), `ratio`, `n_ratio`, `n`,
        and `null`: the `LEVELS` percentiles of `excess` and of `ratio` over `flipped`.
    """
    share = persistence(net_in, net_out, top, keep)
    have = np.isfinite(sharpe_in) & np.isfinite(sharpe_out)
    median, entered = ratio(sharpe_in[have], sharpe_out[have], floor)
    nets, sharpes = flipped(days, np.random.default_rng(SEED))
    shares = [persistence(net_in, row, top, keep) - keep for row in nets]
    ratios = [ratio(sharpe_in[have], row[have], floor)[0] for row in sharpes] if median is not None \
        else None
    return {"share": share, "baseline": keep, "excess": share - keep, "ratio": median,
            "n_ratio": entered, "n": int(net_in.size),
            "null": {"excess": [float(x) for x in np.percentile(shares, LEVELS)],
                     "ratio": ratios and [float(x) for x in np.percentile(ratios, LEVELS)]}}
