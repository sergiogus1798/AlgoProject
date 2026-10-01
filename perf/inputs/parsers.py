"""The reading work the catalogue times: the formats every study opens before it can start."""

from core import barstore, sqxfile, sqxstats, tickfile, trades
from core.datapaths import tick_file
from perf.inputs import sample


def trades_read(cfg: dict) -> dict:
    """Parse a run of exported trade CSVs.

    Args:
        cfg: What config.load() returned.

    Returns:
        Rows parsed and bytes read. Every study starts here, so a regression in this one
        target slows down all of them at once.
    """
    paths = sample.files(cfg, "trades")
    rows = sum(len(trades.read(p)) for p in paths)
    return {"scale": rows, "bytes_in": sample.weight(paths)}


def sqx_xml(cfg: dict) -> dict:
    """Unzip and parse the strategy XML out of a run of .sqx files.

    Args:
        cfg: What config.load() returned.

    Returns:
        Files parsed and bytes read.
    """
    paths = sample.files(cfg, "strategies")
    for p in paths:
        sqxfile.xml(p)
    return {"scale": len(paths), "bytes_in": sample.weight(paths)}


def sqx_stats(cfg: dict) -> dict:
    """Decode the stored statistics block of a run of .sqx files.

    Args:
        cfg: What config.load() returned.

    Returns:
        Files decoded and bytes read. The Java serialisation is walked byte by byte in
        Python, which makes this the most expensive way the project reads a .sqx.
    """
    paths = sample.files(cfg, "strategies")
    for p in paths:
        sqxstats.stats(p)
    return {"scale": len(paths), "bytes_in": sample.weight(paths)}


def bars_read(cfg: dict) -> dict:
    """Read one feed's stored M1 bars into the indexed frame everything aligns on.

    Args:
        cfg: What config.load() returned.

    Returns:
        Bars read and bytes read. Parquet carries the timestamps typed, so this no longer
        measures a date parse — it measures the read the whole bar library is built on.
    """
    path = sample.bars(cfg)
    return {"scale": len(barstore.source(cfg["sample"]["bars_feed"])),
            "bytes_in": sample.weight([path])}


def ticks_read(cfg: dict) -> dict:
    """Decode one SQX tick file into its minute table of spread, as the spread study does.

    Args:
        cfg: What config.load() returned.

    Returns:
        Ticks decoded and bytes read. USDJPY's Darwinex history, the lighter of the two the
        study reads (368 M ticks, 2.6 GB): the cost grows with the file, one pass, no ticks held.
    """
    feed = "USDJPY_TICK"
    _, ticks = tickfile.minutes(feed)
    return {"scale": ticks, "bytes_in": tick_file(feed).stat().st_size}

