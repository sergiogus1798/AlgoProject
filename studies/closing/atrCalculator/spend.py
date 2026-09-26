"""The ledger's side of step 22: ask the door before reading oos2, and leave a row per segment read."""

from ledger import gate, record, study as studymod

STEP = 22
LAUNCHED_BY = "studies.closing.atrCalculator.report"


def allow(symbol: str, segments: list[str]) -> None:
    """Refuse the run before it reads a segment step 22 has no claim on.

    Args:
        symbol: The asset.
        segments: The segments the run is about to read.

    Raises:
        PermissionError: From `ledger.gate.allow`. oos2 is open to step 22 because the owner
            added it to `reserved_for` on 2026-09-26; the look is still spent and recorded.
    """
    for segment in segments:
        gate.allow(STEP, segment, symbol)


def log(symbol: str, timeframe: str, family: str, spans: dict, segments: list[str],
        n: int, cfg: dict, config_hash: str) -> list[dict]:
    """One ledger row per segment the run read.

    Args:
        symbol: The asset.
        timeframe: The strategies' timeframe.
        family: The template family, which names the study with the asset and the clock.
        spans: {segment: (start, end)} as `inputs.windows` returned it.
        segments: The segments that actually had trades.
        n: Strategies read. The study reduces nothing, so it goes in and out unchanged.
        cfg: The run's configuration, for the percentiles it read X at.
        config_hash: The configuration's fingerprint.

    Returns:
        The rows written. Step 22 chooses no strategy, so no scores are passed: the row
        exists to count the look at the segment, not a search among candidates.
    """
    study = studymod.study_id(symbol, timeframe, family)
    return [record.log(study, {
        "step": STEP, "launched_by": LAUNCHED_BY, "symbol": symbol, "timeframe": timeframe,
        "segment": segment, "n_in": n, "n_out": n, "criterion": "atrCalculator/stop",
        "config_hash": config_hash,
        "window_from": str(spans[segment][0]), "window_to": str(spans[segment][1]),
        "thresholds": {"percentiles": cfg["stop"]["percentiles"]},
        "note": "stop X·ATR(20) leído del MAE de las ganadoras del IS; no elige"})
        for segment in segments]
