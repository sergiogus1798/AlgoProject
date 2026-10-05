"""The one read of `oos2` (PLAN §5.5, Q11 d): the door, the ledger's count, the row that spends it."""

from collections.abc import Callable

import numpy as np

from ledger import study, tried, trials as ledger_trials

from .search import trials
from .verdict import deflate


def pool_study(pool: dict) -> str:
    """The ledger study of a declared pool."""
    return f"PORTFOLIO_{pool['hash'][:12]}_construct"


def spent(pool: dict) -> dict | None:
    """The row of the verdict that read this pool's `oos2`, or None while nobody has."""
    frame = study.read(pool_study(pool))
    rows = frame[(frame["step"] == 27) & (frame["segment"] == "oos2")] if len(frame) else frame
    return rows.iloc[0].to_dict() if len(rows) else None


def counted() -> dict:
    """`ledger.trials.overall`: everything the whole project ever tried (owner 2026-10-05, R7)."""
    return ledger_trials.overall([tried.with_sweeps(study.read(s), s) for s in study.studies()])


def read(path: Callable[[], np.ndarray], members: list[str], pool: dict, members_meta: dict,
         criterion: str, launched_by: str, note: str) -> dict:
    """Judge the chosen portfolio on `oos2` by its deflated Sharpe -- once per pool, for good.

    The order is the guarantee: the pool's ledger is asked first, then the one-way door for
    every member's symbol, and only then is `path` called; the row is written whether it
    passes or not. A second call never calls `path`: the same portfolio gets the stored
    reading back, another portfolio of the pool is refused.

    Args:
        path: Returns the portfolio's daily P&L on `oos2`; called at most once.
        members: The chosen portfolio's identities.
        pool: `inputs.pool.read()`'s result (`hash`).
        members_meta: identity -> `{symbol, timeframe, family}` of those members.
        criterion, launched_by: The ledger row's.
        note: What the row should remember besides the figures (a relaxed run's mark).

    Returns:
        `verdict.deflate.read()`'s dict -- N is `counted()["n"]`, sigma the spread of the
        build Sharpes the pool's study holds (`search/trials_real.py` stores them) -- plus
        `stored` (True when it is an earlier read's) and `read_on`; or only `state` and
        `reason` when nothing was read: "refused" (another portfolio spent it) or
        "no_sigma" (the pool's study holds no build Sharpes to deflate by).
    """
    key = "+".join(sorted(members))
    row = spent(pool)
    if row is not None:
        kept = row.get("thresholds") or {}
        if kept.get("members") == key:
            return {**kept, "stored": True, "read_on": row["ts"]}
        return {"state": "refused", "read_on": row["ts"],
                "reason": f"el oos2 de este pool ya lo leyó otra cartera el {row['ts'][:10]}: es "
                          "una sola lectura, de una sola cartera, y está gastada"}
    sigma = ledger_trials.accumulated(study.read(pool_study(pool)))["sigma"]
    if not np.isfinite(sigma) or sigma <= 0:
        return {"state": "no_sigma",
                "reason": "el estudio del pool no guarda Sharpes de build con los que deflactar "
                          "(los escribe la búsqueda por rangos, real.py): oos2 no se abre"}
    trials.admit(members_meta, ["oos2"])
    got = deflate.read(path(), sigma, counted()["n"])
    rows = trials.record_look(
        pool, members_meta, "oos2", criterion, launched_by, got["state"] == "pass",
        f"Sharpe deflactado {got['excess']:+.4f} (N={got['n']}, sigma={got['sigma']:.4f}); {note}",
        {**got, "members": key})
    return {**got, "stored": False, "read_on": rows[0]["ts"]}
