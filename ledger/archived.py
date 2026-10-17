"""The study's search count as the archive freezes it beside a strategy's results."""

from typing import Any, TypedDict

from core.archive.manifest import sha256
from ledger import spend, study, trials


class Ledger(TypedDict):
    """The study's search count at archive time."""

    study: str
    searches: int
    trials: trials.Accumulated
    segments: dict[str, dict[str, Any]]
    sha256: str | None


def ledger(symbol: str, timeframe: str, family: str) -> Ledger:
    """The study's search count at archive time: what deflates this strategy's Sharpe later.

    Args:
        symbol: The asset.
        timeframe: The grid the strategies were built on.
        family: The template family, the third part of the study's id.

    Returns:
        `study`, `searches` (ledger rows), `trials` (`trials.accumulated`: n, sigma, mean,
        unit), `segments` (`spend.virgin`: reads per segment) and the ledger file's sha256,
        None when the study has no ledger yet — which then counts nothing.
    """
    sid = study.study_id(symbol, timeframe, family)
    frame = study.read(sid)
    file = study.path(sid)
    return {
        "study": sid,
        "searches": len(frame),
        "trials": trials.accumulated(frame),
        "segments": spend.virgin(frame, symbol),
        "sha256": sha256(file) if file.exists() else None,
    }
