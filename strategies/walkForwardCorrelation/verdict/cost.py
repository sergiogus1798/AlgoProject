"""What each way of choosing parameters cost on the split that actually happened."""

from collections.abc import Callable

import numpy as np
import pandas as pd

from core.surface import dedupe
from strategies.walkForwardCorrelation.measure import cscv, rules


def landed(train: np.ndarray, test: np.ndarray, grid: pd.DataFrame, rule: Callable,
           rng: np.random.Generator, score: Callable) -> float:
    """The out-of-sample percentile a rule's pick landed in.

    Args:
        train: In-sample returns, periods down and variants across.
        test: Out-of-sample returns over the same variants.
        grid: The `param_` columns in the same order.
        rule: One of `rules.RULES`.
        rng: The draw.
        score: What "best" is measured in, one of `cscv.SCORES`.

    Returns:
        0 to 100. Fifty is what choosing blind would have given, so the number above
        fifty is everything the optimising bought -- which is the question the protocol
        asks and the one a correlation coefficient never answers in units anybody can act
        on.
    """
    pick = rule(score(train), grid, rng)
    outcome = score(test)
    return float((outcome < outcome[pick]).mean() * 100)


def cost(inside: pd.DataFrame, outside: pd.DataFrame, grid: pd.DataFrame, name: str,
         cfg: dict) -> dict:
    """One selection rule's percentile, with the interval the grid actually supports.

    Args:
        inside: The in-sample panel.
        outside: The out-of-sample panel over the same variants.
        grid: The `param_` columns in the panel's column order.
        name: Key of `rules.RULES`.
        cfg: The `cscv` block of config.yaml, which names the score as well as the draws.

    Returns:
        The percentile, its 95 % interval and how many draws are behind it.

        The interval resamples **variants**, through `core.surface.dedupe.bootstrap_ci`,
        because a percentile is a statement about a pool and the pool is what a different
        design would have differed in. The random rule is averaged over many draws; the
        other two are deterministic and need one.
    """
    rule, score = rules.RULES[name], cscv.SCORES[cfg["score"]]
    train, test = inside.to_numpy(), outside.to_numpy()
    draws = cfg["random_draws"] if name == "random_profitable" else 1
    rng = np.random.default_rng(cfg["seed"])
    point = float(np.mean([landed(train, test, grid, rule, rng, score)
                           for _ in range(draws)]))
    low, high = dedupe.bootstrap_ci(
        np.arange(train.shape[1]),
        lambda take: landed(train[:, take], test[:, take], grid.iloc[take], rule,
                            np.random.default_rng(cfg["seed"]), score),
        n_resamples=cfg["bootstrap"], seed=cfg["seed"])
    return {"pct_oos": round(point, 1), "ci95": [round(low, 1), round(high, 1)],
            "draws": draws}


def drift(inside: pd.DataFrame, outside: pd.DataFrame, grid: pd.DataFrame,
          score: Callable) -> dict:
    """How far the best parameter set moved when the window changed.

    Args:
        inside: The in-sample panel.
        outside: The out-of-sample panel.
        grid: The `param_` columns in the panel's column order.
        score: What "best" is measured in, one of `cscv.SCORES`.

    Returns:
        Which variant won in each window and how many levels apart they sit, both as the
        furthest single parameter and as the sum over all of them. A best point that
        moves several levels is a best point that was never a property of the strategy,
        and it is the plainest thing in this whole study to explain to somebody.
    """
    coords = rules.coordinates(grid)
    best_in = int(np.argmax(score(inside.to_numpy())))
    best_out = int(np.argmax(score(outside.to_numpy())))
    moved = np.abs(coords[best_in] - coords[best_out])
    return {"is_best": str(grid.index[best_in]), "oos_best": str(grid.index[best_out]),
            "levels_max": int(moved.max()), "levels_total": int(moved.sum())}
