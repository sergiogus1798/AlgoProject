"""Contract L1: one appended line per search that looked at data and reduced a population."""

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from ledger import gate, study as studymod

REQUIRED = ("step", "launched_by", "symbol", "timeframe", "segment", "n_in", "n_out",
            "criterion")


def distribution(values: np.ndarray) -> dict:
    """The spread of the candidates a search chose from, not just its winner.

    Args:
        values: One score per candidate the search considered, any scale.

    Returns:
        Mean, standard deviation and maximum. `sharpe_std` is the sigma the deflated
        Sharpe needs, and taking it here rather than inside one variant batch is the whole
        point of the ledger: the spread across everything ever tried is wider than the
        spread inside the last thing tried, and the difference always flatters the result.
    """
    clean = np.asarray(values, dtype=float)
    clean = clean[np.isfinite(clean)]
    return {"sharpe_mean": float(clean.mean()), "sharpe_std": float(clean.std(ddof=1)),
            "sharpe_max": float(clean.max()), "n_scored": int(clean.size)}


def search(study: str, row: dict, scores: np.ndarray = None) -> dict:
    """Build one ledger row, checking it says enough to be worth keeping.

    Args:
        study: What `study.study_id` returned.
        row: At least REQUIRED; `thresholds`, `seeds`, `config_hash`, `window_from`,
            `window_to` and `note` are optional but wanted.
        scores: The candidates' scores, if the search ranked anything. **Per observation,
            never annualised** -- SQX stores annualised Sharpes and mixing the two gives a
            deflated Sharpe that looks reasonable and means nothing. `score_unit` records
            which was used and `trials.accumulated` refuses to pool two of them.

    Returns:
        The row, stamped with the study and a UTC timestamp.

    Raises:
        KeyError: A required field is missing. A search that cannot say which segment it
            looked at or how many strategies went in is not a ledger entry, and letting it
            through would make the count it feeds silently wrong.
    """
    missing = [k for k in REQUIRED if k not in row]
    if missing:
        raise KeyError(f"ledger: falta {missing} en la búsqueda del paso {row.get('step')}")
    stamped = {"study": study, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               **{k: None for k in studymod.COLUMNS if k not in ("study", "ts")}, **row}
    scored = distribution(scores) if scores is not None else {}
    return {**stamped, **scored,
            "score_unit": row.get("score_unit", "per_period" if scored else None)}


def append(study: str, row: dict) -> dict:
    """Write one search to the study's ledger.

    Args:
        study: What `study.study_id` returned.
        row: What `search` returned.

    Returns:
        The row as written.

        One JSON object per line, opened in append mode: a line shorter than the pipe
        buffer lands whole even when two sessions write at once, and no reader ever sees
        half a record. **Nothing here rewrites or deletes a line.** A ledger that can be
        edited after the fact answers a different question from the one it was built for.
    """
    file = studymod.path(study)
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, default=str) + "\n")
    return row


def log(study: str, row: dict, scores: np.ndarray = None) -> dict:
    """Check the one-way door, then record the search. The call every module makes.

    Args:
        study: What `study.study_id` returned.
        row: As `search` wants it.
        scores: The candidates' scores, if any.

    Returns:
        The row as written.

    Raises:
        PermissionError: The search reads a reserved segment and is not one of the steps
            it is reserved for. The gate runs **before** the write, so a refused search
            leaves no trace of having been allowed.
    """
    gate.allow(row["step"], row["segment"], row["symbol"])
    return append(study, search(study, row, scores))


def funnel(frame: pd.DataFrame) -> pd.DataFrame:
    """The study's whole funnel, step by step, as it was actually run.

    Args:
        frame: What `study.read` returned.

    Returns:
        One row per search with what entered and what survived, in order. Read down the
        `n_out`/`n_in` column: this is the number the owner asked for -- whether the three
        survivors came out of ten thousand or out of fifty.
    """
    kept = frame[["ts", "step", "criterion", "segment", "n_in", "n_out"]].copy()
    kept["kept"] = (kept["n_out"] / kept["n_in"]).round(4)
    return kept
