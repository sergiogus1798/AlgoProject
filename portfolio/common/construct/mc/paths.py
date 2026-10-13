"""Monte Carlo paths of a combination's server days: joint-daily blocks (D), trade bootstrap (T1, T2).

Every generator returns the same thing: `closed`, `float_end`, `low`, `high` (float64
[n_paths, horizon], account currency at unit risk) and `opened` (int32 [n_paths, horizon]), with
the semantics of the server-day table D of `portfolio/EXECUTION.md` §1 — row p, read from day 0,
is a valid `days` input of `portfolio.funded.rules.machine`.

A `members` item (T1, T2) is `mc.units.units()`'s dict, one per member of the combination:
`low`, `high`, `level` (float32 [Q]: each trade's worst, best and last floating per block since
its entry, trades one after another, unit risk; a trade's last block holds its realised P&L),
`off` (int64 [T + 1]), `pnl` (float64 [T]), `open_day`, `open_slot` (int32 [T], the server day
and the block of it the trade really opened in), `gaps` (int64 [T - 1], blocks from a trade's
close to the next one's open), `per_day` (blocks in a day) and `n_days` (days of history).

| generator | draws | holds fixed |
|---|---|---|
| `daily_blocks` (D) | runs of consecutive days, geometric lengths, the whole history as a circle | each day's figures together (closed, change in floating, intraday low and high, opened): the members' co-movement and the day's own worst moment |
| `trade_bootstrap` (T1) | per member, its trades with replacement and a gap after each | every trade whole, with its floating; nothing between members |
| `trade_blocks` (T2) | windows of history, geometric lengths; every member's trades that opened in one | every trade whole, and which trades of which members opened together and when |
"""

import numpy as np

from . import lay

FIGURES = ("closed", "float_end", "low", "high", "opened")


def indices(n_days: int, horizon: int, n_paths: int, mean_block: float,
            rng: np.random.Generator) -> np.ndarray:
    """The stationary bootstrap's day indices (Politis and Romano), int64 [n_paths, horizon].

    Each step starts a new block at a uniform day with probability 1 / `mean_block`, else
    takes the day after the previous one, the last day followed by the first.
    """
    fresh = rng.random((n_paths, horizon)) < 1.0 / mean_block
    fresh[:, 0] = True
    origin = rng.integers(0, n_days, (n_paths, horizon))
    column = np.arange(horizon)
    since = np.maximum.accumulate(np.where(fresh, column, 0), axis=1)
    return (np.take_along_axis(origin, since, axis=1) + column - since) % n_days


def daily_blocks(days: dict[str, np.ndarray], horizon: int, n_paths: int, mean_block: float,
                 rng: np.random.Generator) -> dict[str, np.ndarray]:
    """D: the joint day table resampled in blocks of consecutive days.

    A drawn day brings its own closed P&L, intraday low and high and trades opened. Floating
    is carried inside a block only, measured from the block's first midnight, and the block's
    last day books what is still floating as closed: a trade cut by a seam is settled there at
    its mark. So a path's equity moves by exactly the mark-to-market P&L of the days drawn,
    and no floating outlives the block it belongs to.

    Args:
        days: A combination's joint server days, `closed`, `float_end`, `low`, `high`,
            `opened`, each [D].
        horizon: Server days per path.
        n_paths: Paths.
        mean_block: Mean block length in days; 1 draws every day independently.
        rng: Source of randomness.

    Returns:
        The five figures, [n_paths, horizon] (module docstring).
    """
    idx = indices(len(days["closed"]), horizon, n_paths, mean_block, rng)
    out = {k: np.asarray(days[k], dtype=np.float64)[idx] for k in ("closed", "low", "high")}
    out["opened"] = np.asarray(days["opened"]).astype(np.int32)[idx]
    seam = np.ones(idx.shape, dtype=bool)
    seam[:, 1:] = idx[:, 1:] != idx[:, :-1] + 1
    column = np.arange(horizon)
    first = np.take_along_axis(idx, np.maximum.accumulate(np.where(seam, column, 0), axis=1), axis=1)
    before = np.concatenate([[0.0], np.asarray(days["float_end"], dtype=np.float64)])
    floating = before[idx + 1] - before[first]
    last = np.zeros(idx.shape, dtype=bool)
    last[:, :-1] = seam[:, 1:]
    out["closed"] = out["closed"] + np.where(last, floating, 0.0)
    out["float_end"] = np.where(last, 0.0, floating)
    return out


def path_seeds(n: int, rng: np.random.Generator) -> np.ndarray:
    """One kernel seed per path, all different, uint64 [n].

    numba's `np.random.seed` keeps 32 bits of whatever it is given, so the seeds are drawn from
    [0, 2**32) WITHOUT replacement: no two paths share a stream. With replacement (until
    2026-10-13) a million paths held ~116 repeated pairs. The paths' distribution is the same;
    the draws are not, so paths stored before that date do not reproduce from their seed
    (owner, 2026-10-13, encargo 66 §9).
    """
    return rng.choice(2**32, n, replace=False).astype(np.uint64)


def _empty(n_paths: int, horizon: int) -> dict[str, np.ndarray]:
    """Zeroed output arrays for the laying kernels."""
    out = {k: np.zeros((n_paths, horizon)) for k in FIGURES[:4]}
    out["opened"] = np.zeros((n_paths, horizon), dtype=np.int32)
    return out


def trade_bootstrap(members: list[dict], horizon: int, n_paths: int,
                    rng: np.random.Generator) -> dict[str, np.ndarray]:
    """T1: each member's trades with replacement, end to end, members independent.

    A member's path starts inside a gap (a uniform share of a gap drawn from its history),
    then alternates a drawn trade and a drawn gap; the next trade opens the drawn number of
    blocks after the previous one closed, whatever the hour that falls on.

    Args:
        members: One `mc.units.units()` dict per member (module docstring).
        horizon: Server days per path.
        n_paths: Paths.
        rng: Source of randomness; the paths are reproducible from it.

    Returns:
        The five figures, [n_paths, horizon] (module docstring).
    """
    short = [i for i, m in enumerate(members) if len(m["gaps"]) == 0]
    if short:
        raise ValueError(f"T1: los miembros {short} tienen menos de 2 operaciones: sin huecos que sortear")
    flat = lay.stack(members)
    out = _empty(n_paths, horizon)
    seeds = path_seeds(n_paths, rng)
    lay.t1(flat["start"], flat["n"], flat["pnl"], flat["low"], flat["high"], flat["level"],
           flat["first"], flat["gaps"], flat["gap_first"], seeds, members[0]["per_day"],
           out["closed"], out["float_end"], out["low"], out["high"], out["opened"])
    return out


def trade_blocks(members: list[dict], horizon: int, n_paths: int, window_days: int,
                 rng: np.random.Generator) -> dict[str, np.ndarray]:
    """T2: windows of history; every member's trades that opened in one, together, each whole.

    A window is a run of consecutive server days of geometric length, mean `window_days`, the
    history taken as a circle. Each trade keeps the day of the window and the block of the day
    it really opened in; one that outlives its window runs on into the next.

    Args:
        members: One `mc.units.units()` dict per member (module docstring).
        horizon: Server days per path.
        n_paths: Paths.
        window_days: Mean window length in server days.
        rng: Source of randomness; the paths are reproducible from it.

    Returns:
        The five figures, [n_paths, horizon] (module docstring).
    """
    flat = lay.by_day(lay.stack(members), members[0]["n_days"])
    out = _empty(n_paths, horizon)
    seeds = path_seeds(n_paths, rng)
    lay.t2(flat["start"], flat["n"], flat["pnl"], flat["open_slot"], flat["low"], flat["high"],
           flat["level"], flat["day_ptr"], seeds, float(window_days), members[0]["per_day"],
           out["closed"], out["float_end"], out["low"], out["high"], out["opened"])
    return out


def history(members: list[dict]) -> dict[str, np.ndarray]:
    """The members' trades laid where they really were: the server days the units rebuild, [D]."""
    flat = lay.stack(members)
    n_days = members[0]["n_days"]
    out = {k: v[0] for k, v in _empty(1, n_days).items()}
    lay.replay(flat["start"], flat["n"], flat["pnl"], flat["open_day"], flat["open_slot"],
               flat["low"], flat["high"], flat["level"], members[0]["per_day"], out["closed"],
               out["float_end"], out["low"], out["high"], out["opened"])
    return out
