"""The funded search's stage A objective: P(pass) of a plan per combination, over a risk grid."""

import numba
import numpy as np

from portfolio.funded.rules.machine import _MINDAYS, _RISK, _stage_matrix, _sweep_kernel


def evaluate(data: dict, combos: np.ndarray, plan: dict, cfg: dict) -> np.ndarray:
    """P(pass within the horizon) of `plan`, per combination and risk level.

    Args:
        data: `stagea_data.prepare()` output.
        combos: int32 [M, K_max], member row indices into `data`, padded with -1.
        plan: A `catalog.plan()` dict.
        cfg: The construct config (`funded.risk_grid`, `funded.horizon_days`, `funded.min_lot`).

    Returns:
        float64 [M, L] — one column per `cfg["funded"]["risk_grid"]` level; NaN where the level
        is infeasible for that combination (its tightest member's lot below `min_lot / 2`).
    """
    grid = np.asarray(cfg["funded"]["risk_grid"], dtype=np.float64)
    horizon = int(cfg["funded"]["horizon_days"])
    min_lot = float(cfg["funded"]["min_lot"])
    size = float(plan["size"])
    stage_names = [s["stage"] for s in plan["stages"] if s["stage"] != "funded"]
    stagemat_base = _stage_matrix(plan, {s: 1.0 for s in stage_names})
    if np.any(stagemat_base[:, _MINDAYS] < 0):
        raise NotImplementedError("evaluate: a challenge stage has no known min_days")
    n_days = data["closed"].shape[1]
    starts = np.arange(0, max(n_days - horizon + 1, 0), dtype=np.int64)
    out = np.full((combos.shape[0], grid.shape[0]), np.nan)
    _evaluate_kernel(data["closed"], data["float_end"], data["opened"].astype(np.int64),
                      data["low5"], data["high5"], data["block_day"].astype(np.int64),
                      data["lot_unit"], combos.astype(np.int32), stagemat_base, grid, size,
                      min_lot, starts, horizon, out)
    return out


def best(scores: np.ndarray, grid: list[float]) -> tuple[np.ndarray, np.ndarray]:
    """Each row's best P(pass) and the risk level it was reached at.

    Args:
        scores: `evaluate()` output.
        grid: The risk levels its columns follow.

    Returns:
        `(best_p, best_r)`, each length `scores.shape[0]`; NaN where every level was infeasible.
    """
    grid_arr = np.asarray(grid, dtype=np.float64)
    filled = np.where(np.isnan(scores), -np.inf, scores)
    idx = np.argmax(filled, axis=1)
    rows = np.arange(scores.shape[0])
    best_p = scores[rows, idx]
    best_r = grid_arr[idx]
    all_nan = np.all(np.isnan(scores), axis=1)
    return np.where(all_nan, np.nan, best_p), np.where(all_nan, np.nan, best_r)


@numba.njit(parallel=True, cache=True)
def _evaluate_kernel(closed: np.ndarray, float_end: np.ndarray, opened: np.ndarray,
                      low5: np.ndarray, high5: np.ndarray, block_day: np.ndarray,
                      lot_unit: np.ndarray, combos: np.ndarray, stagemat_base: np.ndarray,
                      risk_grid: np.ndarray, size: float, min_lot: float, starts: np.ndarray,
                      horizon: int, out: np.ndarray) -> None:
    """One combination per thread: joint day arrays, then the rule machine per risk level."""
    m_total, k_max = combos.shape
    n_days = closed.shape[1]
    n_blocks = low5.shape[1]
    n_levels = risk_grid.shape[0]
    n_starts = starts.shape[0]
    for m in numba.prange(m_total):
        k = 0
        for kk in range(k_max):
            if combos[m, kk] < 0:
                break
            k += 1
        closed_sum = np.zeros(n_days)
        float_sum = np.zeros(n_days)
        opened_sum = np.zeros(n_days, dtype=np.int64)
        min_lot_unit = np.inf
        for kk in range(k):
            i = combos[m, kk]
            for dd in range(n_days):
                closed_sum[dd] += closed[i, dd]
                float_sum[dd] += float_end[i, dd]
                opened_sum[dd] += opened[i, dd]
            if lot_unit[i] < min_lot_unit:
                min_lot_unit = lot_unit[i]
        day_low = np.zeros(n_days)
        day_high = np.zeros(n_days)
        seen = np.zeros(n_days, dtype=np.bool_)
        for b in range(n_blocks):
            s_low = 0.0
            s_high = 0.0
            for kk in range(k):
                i = combos[m, kk]
                s_low += low5[i, b]
                s_high += high5[i, b]
            dd = block_day[b]
            if not seen[dd]:
                day_low[dd] = s_low
                day_high[dd] = s_high
                seen[dd] = True
            else:
                if s_low < day_low[dd]:
                    day_low[dd] = s_low
                if s_high > day_high[dd]:
                    day_high[dd] = s_high
        for ell in range(n_levels):
            r = risk_grid[ell]
            if k == 0 or min_lot_unit * r * size < min_lot / 2:
                out[m, ell] = np.nan
                continue
            stagemat = stagemat_base.copy()
            for si in range(stagemat.shape[0]):
                stagemat[si, _RISK] = r * size
            outcomes = _sweep_kernel(closed_sum, float_sum, day_low, day_high, opened_sum,
                                      stagemat, starts, size, horizon)
            passes = 0
            for si in range(n_starts):
                if outcomes[si] == 1:
                    passes += 1
            out[m, ell] = passes / n_starts if n_starts > 0 else np.nan
