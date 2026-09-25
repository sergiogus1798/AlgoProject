"""Where the real files a measurement runs on are found, so two dates measure the same thing."""

from pathlib import Path

from core.paths import DATA, bar_source


def export(cfg: dict, databank: str) -> Path:
    """The newest dated export of one databank.

    Args:
        cfg: What config.load() returned.
        databank: Directory name under the project, e.g. "OOS".

    Returns:
        Path to the latest YYYY-MM-DD directory. Newest rather than pinned, because an
        export is immutable and a pinned date would rot the catalogue the first time the
        owner re-exports.
    """
    if not databank:
        raise SystemExit("perf/config.yaml: sample.trades_databank is empty — choose an export with "
                         "trades/ and strategies/ (MC_Trades was deleted 2026-09-25)")
    where = DATA / "raw" / cfg["sample"]["project"] / databank
    return max(d for d in where.iterdir() if d.is_dir())


def files(cfg: dict, kind: str) -> list[Path]:
    """The files a per-file target reads, in a fixed order.

    Args:
        cfg: What config.load() returned.
        kind: "trades" for the exported CSVs, "strategies" for the .sqx beside them.

    Returns:
        The first `sample.files` of that directory sorted by name. Sorted, not sampled:
        a random subset would put the measurement's noise in the file list instead of in
        the clock.
    """
    where = export(cfg, cfg["sample"]["trades_databank"]) / kind
    return sorted(where.iterdir())[:cfg["sample"]["files"]]


def bars(cfg: dict) -> Path:
    """The bar file the market-level targets run on.

    Args:
        cfg: What config.load() returned.

    Returns:
        Path to the configured feed's M1 Parquet, the only bar data the project stores.
        Every other timeframe is resampled from it, so this is what a bar-reading cost is
        measured on.
    """
    return bar_source(cfg["sample"]["bars_feed"])


def weight(paths: list[Path]) -> int:
    """Bytes a target had to read.

    Args:
        paths: Every file it opened.

    Returns:
        Total size in bytes. Stored with the measurement so a time that grew because the
        data grew is not read as code that got slower.
    """
    return sum(p.stat().st_size for p in paths)
