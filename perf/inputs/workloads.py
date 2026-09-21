"""The real analysis work the catalogue times: one call each, on data already on disk."""

from pathlib import Path

from core import bars
from perf.inputs import sample
from strategies.monteCarlo.inputs import config as mc_config
from strategies.monteCarlo.inputs import costs, stream
from strategies.monteCarlo.model import regime
from strategies.monteCarlo import run
from strategies.crossmarket.simulate import paired
from strategies.retest.measure import store


def montecarlo_stream(cfg: dict) -> dict:
    """Turn one strategy's exported trades into the arrays every family runs on.

    Args:
        cfg: What config.load() returned.

    Returns:
        Trades built and bytes read.
    """
    path = sample.files(cfg, "trades")[0]
    asset = costs.load(cfg["sample"]["asset"])
    mc = mc_config.load()
    source = stream.build(path, asset, mc["global"]["risk_per_trade"])
    return {"scale": int(source["pnl"].size), "bytes_in": sample.weight([path])}


def _analyse(path: Path, cfg: dict) -> dict:
    """One trade file through every Monte Carlo family, at the catalogue's budget.

    Args:
        path: The exported trade CSV of one strategy.
        cfg: What config.load() returned.

    Returns:
        Trades analysed and bytes read. The budget is `sample.n_sims`, not the study's own:
        the catalogue measures the shape of the cost, and the cost is linear in simulations.
    """
    bar_file = sample.bars(cfg)
    asset = costs.load(cfg["sample"]["asset"])
    mc = mc_config.load([f"global.n_sims={cfg['sample']['n_sims']}"])
    source = stream.build(path, asset, mc["global"]["risk_per_trade"])
    run.analyse(source, regime.daily(bars.read(bar_file)), asset, mc)
    return {"scale": int(source["pnl"].size), "bytes_in": sample.weight([path, bar_file])}


def montecarlo_analyse(cfg: dict) -> dict:
    """One strategy through every Monte Carlo family, at the catalogue's simulation budget.

    Args:
        cfg: What config.load() returned.

    Returns:
        Trades analysed and bytes read, for the first file of the export.
    """
    return _analyse(sample.files(cfg, "trades")[0], cfg)


def montecarlo_analyse_long(cfg: dict) -> dict:
    """The export's longest strategy through every Monte Carlo family.

    Args:
        cfg: What config.load() returned.

    Returns:
        Trades analysed and bytes read. A worker's memory grows with the trade count, so
        the short strategy and the longest one are two points of one curve, not one number.
    """
    where = sample.export(cfg, cfg["sample"]["trades_databank"]) / "trades"
    return _analyse(max(where.iterdir(), key=lambda p: p.stat().st_size), cfg)


def retest_load_sims(cfg: dict) -> dict:
    """Read back the whole simulation table of one ingested retest battery.

    Args:
        cfg: What config.load() returned.

    Returns:
        Rows loaded and bytes on disk. This is the read path the retest study repeats on
        every run, and the one a change of parquet layout would move.
    """
    where = sample.export(cfg, cfg["sample"]["retest_databank"])
    frame = store.load_sims(cfg["sample"]["project"], cfg["sample"]["retest_databank"],
                            where.name)
    size = sum(p.stat().st_size for p in (where / store.SIMS).rglob("*.parquet"))
    return {"scale": len(frame), "bytes_in": size}


def crossmarket_paired(cfg: dict) -> dict:
    """The blind-window reference the cross-market study builds for every holding period.

    Args:
        cfg: What config.load() returned.

    Returns:
        Bars covered and bytes read. Run over the same spread of holding periods the study
        uses, because the cost of this kernel is one pass per period, not one in total.
    """
    path = sample.bars(cfg)
    frame = bars.read(path)
    enter, leave = frame["Open"].to_numpy(), frame["Close"].to_numpy()
    for hold in (8, 16, 32, 64, 128):
        paired.centered_means(enter, leave, hold, half=1000)
    return {"scale": len(frame), "bytes_in": sample.weight([path])}
