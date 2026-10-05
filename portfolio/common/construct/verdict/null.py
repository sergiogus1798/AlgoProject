"""Where the chosen combination sits among the selected null's winners."""

import numpy as np


def percentile(chosen: float, null: np.ndarray) -> float:
    """The share of the null at or below the chosen figure, ties counted half.

    Args:
        chosen: The chosen combination's figure on the judging stretch.
        null: The same figure for each null search's own winner.

    Returns:
        In [0, 1]; uniform over repeated experiments when the chosen one is itself a draw of
        the null (the mid-rank keeps it so when figures tie, as shares of few paths do).
    """
    null = np.asarray(null, dtype=float)
    return float(((null < chosen).sum() + 0.5 * (null == chosen).sum()) / null.size)


def read(chosen: dict[str, float], null: list[dict[str, float]]) -> dict[str, dict]:
    """Every measure of the chosen combination against the null's distribution of it.

    Args:
        chosen: measure -> the chosen combination's value.
        null: One such dict per null search (its winner, judged the same way).

    Returns:
        measure -> `value`, `percentile`, `null_median`, `null_p95`, `null_max`, `n`.
    """
    out = {}
    for name, value in chosen.items():
        draws = np.array([n[name] for n in null], dtype=float)
        out[name] = {"value": float(value), "percentile": percentile(value, draws),
                     "null_median": float(np.median(draws)),
                     "null_p95": float(np.percentile(draws, 95)),
                     "null_max": float(draws.max()), "n": int(draws.size)}
    return out


def bar(chosen: float, draws: np.ndarray, quantile: float, share_chosen: float) -> dict:
    """The real path's oos1 reading (Q11 d): the chosen figure against a percentile of the null's.

    A null that keeps redrawing the chosen portfolio cannot be beaten by it: when the chosen
    one is itself at least the top `100 - quantile` % of the draws, the bar is its own figure.
    That is said (`no_discrimina`), never printed as a percentile.

    Args:
        chosen: The chosen portfolio's figure.
        draws: The same figure for each null draw.
        quantile: The percentile of `draws` to beat, 0-100.
        share_chosen: The share of the draws that are the chosen portfolio itself.

    Returns:
        `value`, `bar` (that percentile of the draws), `percentile` (mid-rank of the chosen
        one among them), `null_median`, `n`, `quantile`, `share_chosen` and `state`:
        "no_discrimina", else "pass" when `value` > `bar`, else "fail".
    """
    draws = np.asarray(draws, dtype=float)
    level = float(np.percentile(draws, quantile))
    if share_chosen >= (100 - quantile) / 100:
        state = "no_discrimina"
    else:
        state = "pass" if chosen > level else "fail"
    return {"value": float(chosen), "bar": level, "percentile": percentile(chosen, draws),
            "null_median": float(np.median(draws)), "n": int(draws.size),
            "quantile": float(quantile), "share_chosen": float(share_chosen), "state": state}
