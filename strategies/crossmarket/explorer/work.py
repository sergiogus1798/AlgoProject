"""What a button runs, and the one place a finished analysis is held for the session."""

from pathlib import Path

from strategies.crossmarket import views
from strategies.crossmarket.explorer import analysis, jobs

# The session's results, one entry per strategy. Deliberately memory only: the owner asked
# that a number on screen always come from the run he just pressed, never from a stored one,
# so there is no cache, no staleness flag and nothing on disk to go out of date.
RESULTS: dict = {}


def available(setup: dict, name: str) -> list[dict]:
    """Which markets this strategy actually traded on, and which it did not.

    Args:
        setup: What serve.main() assembled.
        name: Strategy name.

    Returns:
        One row per market of the universe, with `traded` saying whether the export carries
        trades for this strategy there. A market the strategy never fired on has no file at
        all — that is a result about the strategy, not a missing input, and it is shown
        rather than hidden.
    """
    return [{**m, "traded": (setup["trades"] / m["feed"] / f"{name}.csv").exists()}
            for m in setup["universe"]["markets"]]


def analyse(setup: dict, cfg: dict, name: str, only: str | None) -> dict:
    """Run the analysis of one strategy, or of one of its markets.

    Args:
        setup: What serve.main() assembled.
        cfg: The run configuration.
        name: Strategy name.
        only: One market feed, or None for all of them.

    Returns:
        A short summary for the status line. The record goes into RESULTS. A single-market
        run merges into whatever is already there for that strategy instead of replacing it,
        so re-running one market at 50,000 draws does not throw away the other.
    """
    record = analysis.analyse_strategy(setup, cfg, name, only, jobs.step)
    if only is not None and name in RESULTS:
        record = merged(RESULTS[name], record, only, cfg)
    RESULTS[name] = {**record, "cfg": cfg}
    return {"strategy": name, "markets": len(record["rows"])}


def clear(data_root: Path) -> int:
    """Delete any cross-market results a previous build left on disk.

    Args:
        data_root: The data root.

    Returns:
        How many files were removed. Nothing here writes to disk any more, but earlier
        versions cached under `derived/crossmarket/`; leaving those behind would let someone
        believe a stale number came from this session.
    """
    folder = data_root / "derived" / "crossmarket"
    if not folder.exists():
        return 0
    files = list(folder.rglob("*.json"))
    for f in files:
        f.unlink()
    for d in sorted(folder.rglob("*"), reverse=True):
        if d.is_dir():
            d.rmdir()
    folder.rmdir()
    return len(files)


def merged(old: dict, fresh: dict, feed: str, cfg: dict) -> dict:
    """One market's new result folded into the record the session already had.

    Args:
        old: The record in RESULTS for this strategy.
        fresh: What analyse_strategy() returned for the single market.
        feed: The market that was re-run.
        cfg: The configuration that run was made with.

    Returns:
        A record holding every market again — the re-run one from `fresh` and the rest from
        `old`. The strategy-level views are **rebuilt**, not carried over: a correlation
        matrix or a combined account still describing the previous version of this market
        would be wrong without ever looking stale.
    """
    rows = sorted([r for r in old["rows"] if r["feed"] != feed] + fresh["rows"],
                  key=lambda r: r["feed"])
    weekly = {**old["weekly"], **fresh["weekly"]}
    streams = {**old["streams"], **fresh["streams"]}
    runs = {**old["runs"], **fresh["runs"]}
    # `oos` is not recomputed by a single-market run — it is the base asset's own stretch
    # and no market button touches it — so the one the session already has is carried.
    return {**fresh, "rows": rows, "runs": runs, "oos": old["oos"],
            "equity": {**old["equity"], **fresh["equity"]}, "weekly": weekly,
            "streams": streams, **views.build(weekly, streams, runs, cfg)}
