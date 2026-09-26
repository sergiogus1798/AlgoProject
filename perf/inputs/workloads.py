"""The real analysis work the catalogue times: one call each, on data already on disk."""

from pathlib import Path

from core import bars
from engines.regimes import regime
from perf.inputs import sample
from portfolio.common.monteCarlo import run
from portfolio.common.monteCarlo.inputs import config as mc_config, costs, stream
from engines.inference.snooping import superior
from studies.breakage.mcRetest.measure import store
from studies.closing.atrCalculator import inputs as atr_inputs, load as atr_load, one as atr_one
from studies.data.feedQuality import detect as fq_detect, inputs as fq_inputs
from studies.screening.snoopingScreen import inputs as snooping
from studies.transfer.crossmarket.simulate import paired


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


def atrcalculator_reading(cfg: dict) -> dict:
    """The ATR stop study's reading (§2) on every strategy of one export, bootstrap included.

    Args:
        cfg: What config.load() returned.

    Returns:
        Trades read and bytes read. The bootstrap of the percentiles is the cost that
        grows, linear in winners times resamples.
    """
    s = cfg["sample"]
    study = atr_inputs.config([])
    got = atr_load.load(s["project"], [s["atr_databank"]], s["bars_feed"], s["asset"],
                        s["atr_timeframe"], None, study)
    for name in got["strategies"]:
        atr_one.run(name, got, study)
    return {"scale": len(got["trades"]), "bytes_in": sample.weight(got["packed"])}


def snooping_superior(cfg: dict) -> dict:
    """The SPA and the StepM over one gate harvest's daily panel, at the study's own settings.

    Args:
        cfg: What config.load() returned.

    Returns:
        Panel cells (days × strategies) tested and bytes read. The panel is the raw one,
        without the benchmark subtracted: the cost is the bootstrap's, and it does not
        depend on what the columns hold.
    """
    project, databank, asset = cfg["sample"]["harvest"]
    folder = snooping.harvest(project, databank)
    panel = snooping.panel(folder, snooping.window(asset, "oos1"))
    boot, fwer = snooping.config([])["bootstrap"], snooping.config([])["stepm"]["fwer"]
    block = superior.block_length(panel)
    superior.spa(panel, block, boot["reps"], boot["seed"])
    superior.stepm(panel, fwer, block, boot["reps"], boot["seed"])
    return {"scale": int(panel.size), "bytes_in": sample.weight([folder / "equity.parquet"])}


def feedquality_detect(cfg: dict) -> dict:
    """One feed through the feed-quality detector: the trailing scale, the spikes, the runs.

    Args:
        cfg: What config.load() returned.

    Returns:
        Bars read. The scale is the cost that grows: one median per hour of the week per
        week of history, linear in the feed's length.
    """
    feed = cfg["sample"]["bars_feed"]
    study = fq_inputs.config([])
    b = fq_inputs.bars(feed)
    got = fq_detect.measure(b, fq_inputs.tick(b, study["session"]["years"]), study)
    fq_detect.events(b, got, study["K"][feed], fq_inputs.week_mask(study, feed), study)
    return {"scale": len(b["c"]), "bytes_in": int(sum(b[x].nbytes for x in "ohlc"))}
