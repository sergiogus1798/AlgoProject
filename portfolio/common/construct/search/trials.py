"""The funded path's ledger rows: the pool's own study, and one row in every member's own study."""

import numpy as np

from ledger import gate, record as ledger_record
from ledger.study import study_id


def record(run: dict, pool: dict, plan_key: str, members_meta: dict, cfg: dict) -> list[dict]:
    """Log the search: one row in `PORTFOLIO_<pool>_construct`, one in each member's study.

    Args:
        run: `genetic.run`'s result -- `members`, `score`, `best`; optionally `level` (the
            risk level, same length as `score`, `funded.py`'s side channel from `stagea.best`).
        pool: `inputs.pool.read`'s result (`hash`).
        plan_key: The funded plan searched against, e.g. "hantec:express:2000:USD".
        members_meta: identity -> `{symbol, timeframe, family}`, one entry per admissible
            member the search read (`n_in`).
        cfg: The run's config: its relaxed thresholds and open-risk cap go in the row's note.

    Returns:
        Every row appended, the pool's row first.
    """
    scores = np.asarray(run["score"], dtype=float)
    identities = list(members_meta)
    symbols = "+".join(sorted({m["symbol"] for m in members_meta.values()}))
    pool_study = f"PORTFOLIO_{pool['hash'][:12]}_construct"
    base = {"step": 27, "launched_by": "funded", "segment": "build", "n_in": len(identities),
            "n_out": int(run["best"]["members"].size), "criterion": f"portfolio/funded/{plan_key}",
            "score_unit": "p_pass", "note": f"relaxed={cfg.get('relaxed') or 'no'}; "
                                            f"open_risk_cap={cfg.get('funded', {}).get('open_risk_cap')}"}
    rows = [ledger_record.log(pool_study, {**base, "symbol": symbols, "timeframe": "mixed"}, scores)]
    for identity in identities:
        meta = members_meta[identity]
        sid = study_id(meta["symbol"], meta["timeframe"], meta["family"])
        rows.append(ledger_record.log(
            sid, {**base, "symbol": meta["symbol"], "timeframe": meta["timeframe"]}, scores))
    return rows


def _both(pool: dict, members_meta: dict, base: dict, scores: np.ndarray | None) -> list[dict]:
    """One row in `PORTFOLIO_<pool>_construct` and one in each member's own study (Q12)."""
    symbols = "+".join(sorted({m["symbol"] for m in members_meta.values()}))
    rows = [ledger_record.log(f"PORTFOLIO_{pool['hash'][:12]}_construct",
                              {**base, "symbol": symbols, "timeframe": "mixed"}, scores)]
    for meta in members_meta.values():
        sid = study_id(meta["symbol"], meta["timeframe"], meta["family"])
        rows.append(ledger_record.log(
            sid, {**base, "symbol": meta["symbol"], "timeframe": meta["timeframe"]}, scores))
    return rows


def admit(members_meta: dict, segments: list[str]) -> None:
    """Ask the one-way door for every segment and member symbol, before any of it is opened."""
    for segment in segments:
        for symbol in sorted({m["symbol"] for m in members_meta.values()}):
            gate.allow(27, segment, symbol)


def record_b(stage_b: dict, pool: dict, plan_key: str, members_meta: dict) -> list[dict]:
    """Log stage B: one search per plan, its candidates the shortlist times the risk settings.

    Args:
        stage_b: `stageb_run.run()`'s result (`rows`, `table`, `winner`, `n_settings`).
        pool: `inputs.pool.read()`'s result (`hash`).
        plan_key: The funded plan.
        members_meta: identity -> `{symbol, timeframe, family}`, the strategies of the
            shortlist (`n_in`).

    Returns:
        Every row appended, the pool's first. `scores` are each candidate's deciding P(pass):
        per combination and risk setting, the lowest over the Monte Carlos and block lengths.
    """
    scores = stage_b["rows"].groupby(["members", "setting"])["p_pass"].min().to_numpy()
    base = {"step": 27, "launched_by": "funded_b", "segment": "build",
            "n_in": len(members_meta), "n_out": int(stage_b["winner"]["k"]),
            "criterion": f"portfolio/funded_b/{plan_key}", "score_unit": "p_pass",
            "note": f"{len(stage_b['table'])} carteras x {stage_b['n_settings']} riesgos"}
    return _both(pool, members_meta, base, scores)


def record_look(pool: dict, members_meta: dict, segment: str, criterion: str, launched_by: str,
                passed: bool | None, note: str, reading: dict | None = None) -> list[dict]:
    """Log one look of a verdict at one segment (PLAN §6): the pool's study and each member's.

    Args:
        pool: `inputs.pool.read()`'s result (`hash`).
        members_meta: The chosen members only.
        segment: The segment the verdict read: one row per look per segment.
        criterion: `portfolio/verdict/<null>` or `portfolio/funded_verdict/<plan>`.
        passed: What the look decided; None when it could decide nothing.
        note: The look in words: the null, the figures, a relaxed run's mark.
        reading: The figures read, kept in the row's `thresholds` -- on the one-read segment it is the
            one stored reading a later verdict is answered with.

    Returns:
        Every row appended, the pool's first: `n_in` 1 portfolio, `n_out` 1 unless it failed.
    """
    base = {"step": 27, "launched_by": launched_by, "segment": segment, "n_in": 1,
            "n_out": 0 if passed is False else 1, "criterion": criterion, "note": note,
            "thresholds": reading}
    return _both(pool, members_meta, base, None)


def record_rows(pool: dict, members_meta: dict, base: dict, scores: np.ndarray | None = None) -> list[dict]:
    """Log a step-27 study that is neither a search nor a verdict's look (the weight walk-forward, incubation).

    Args:
        pool: `inputs.pool.read()`'s result (`hash`).
        members_meta: The members the study read.
        base: The row but `step`, `symbol` and `timeframe`: `launched_by`, `segment`, `n_in`,
            `n_out`, `criterion`, `note`.
        scores: One figure per configuration compared on the segment; `n_scored` counts them.

    Returns:
        Every row appended, the pool's first.
    """
    return _both(pool, members_meta, {"step": 27, **base}, scores)
