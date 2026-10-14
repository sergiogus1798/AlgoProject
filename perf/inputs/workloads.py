"""The real analysis work the catalogue times: one call each, on data already on disk."""

from pathlib import Path

import pandas as pd

from core import assetdata, bars, trades
from core.paths import DATA, harvest_dir
from engines.regimes import regime
from perf.inputs import sample
from portfolio.common.monteCarlo import run
from portfolio.common.monteCarlo.inputs import config as mc_config, costs, stream
from engines.inference.snooping import superior
from pipeline.autopilot import facts
from studies.breakage.mcRetest.measure import store
from studies.data.feedQuality import detect as fq_detect, inputs as fq_inputs
from studies.research.pooledProfile import inputs as pooled_inputs, one as pooled_one
from studies.research.profilePower import inputs as power_inputs, one as power_one
from studies.screening.falsePositives import (
    chain as fp_chain,
    inputs as fp_inputs,
    model as fp_model,
)
from studies.closing.blindJoint import inputs as joint
from ui.daemon.workflow import sources


def montecarlo_stream(cfg: dict) -> sample.Workload:
    """Turn one strategy's exported trades into the arrays every family runs on.

    Args:
        cfg: What config.load() returned.

    Returns:
        Trades built and bytes read.
    """
    path = sample.files(cfg, "trades")[0]
    asset = costs.load(cfg["sample"]["asset"])
    mc = mc_config.load()
    source = stream.build(
        trades.read(path), path.stem, asset, mc["global"]["risk_per_trade"]
    )
    return {"scale": int(source["pnl"].size), "bytes_in": sample.weight([path])}


def _analyse(path: Path, cfg: dict) -> sample.Workload:
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
    mc = mc_config.load([f"global.n_sims={cfg['sample']['n_sims']}", "global.seed=0"])
    source = stream.build(
        trades.read(path), path.stem, asset, mc["global"]["risk_per_trade"]
    )
    run.analyse(source, regime.daily(bars.read(bar_file)), asset, mc)
    return {
        "scale": int(source["pnl"].size),
        "bytes_in": sample.weight([path, bar_file]),
    }


def montecarlo_analyse(cfg: dict) -> sample.Workload:
    """One strategy through every Monte Carlo family, at the catalogue's simulation budget.

    Args:
        cfg: What config.load() returned.

    Returns:
        Trades analysed and bytes read, for the first file of the export.
    """
    return _analyse(sample.files(cfg, "trades")[0], cfg)


def montecarlo_analyse_long(cfg: dict) -> sample.Workload:
    """The export's longest strategy through every Monte Carlo family.

    Args:
        cfg: What config.load() returned.

    Returns:
        Trades analysed and bytes read. A worker's memory grows with the trade count, so
        the short strategy and the longest one are two points of one curve, not one number.
    """
    where = sample.export(cfg, cfg["sample"]["trades_databank"]) / "trades"
    return _analyse(max(where.iterdir(), key=lambda p: p.stat().st_size), cfg)


def retest_load_sims(cfg: dict) -> sample.Workload:
    """Read back the whole simulation table of one ingested retest battery.

    Args:
        cfg: What config.load() returned.

    Returns:
        Rows loaded and bytes on disk. This is the read path the retest study repeats on
        every run, and the one a change of parquet layout would move.
    """
    where = sample.export(cfg, cfg["sample"]["retest_databank"])
    frame = store.load_sims(
        cfg["sample"]["project"], cfg["sample"]["retest_databank"], where.name
    )
    size = sum(p.stat().st_size for p in (where / store.SIMS).rglob("*.parquet"))
    return {"scale": len(frame), "bytes_in": size}


def snooping_superior(cfg: dict) -> sample.Workload:
    """The SPA and the StepM over one gate harvest's daily panel, at step 20's settings.

    Args:
        cfg: What config.load() returned.

    Returns:
        Panel cells (days × strategies) tested and bytes read. The panel is SQX's stored
        curve differenced, without the benchmark subtracted: the cost is the bootstrap's,
        whatever the columns hold.
    """
    project, databank, asset = cfg["sample"]["harvest"]
    folder = sorted(
        (DATA / "harvest" / project / databank.replace(" ", "_")).glob("[0-9]*/")
    )[-1]  # a day, never `_aparte`
    lo, hi = (
        pd.Timestamp(t, unit="ms")
        for t in assetdata.window(assetdata.load(asset), "oos1")
    )
    curve = pd.read_parquet(folder / "equity.parquet")
    curve = curve[curve["sample"] == "OOS"].pivot(
        index="day", columns="identity", values="equity"
    )
    panel = (
        curve[(curve.index >= lo) & (curve.index < hi)]
        .ffill()
        .diff()
        .iloc[1:]
        .fillna(0.0)
    )
    conf, block = joint.config([]), superior.block_length(panel)
    boot, fwer = conf["bootstrap"], conf["stepm"]["fwer"]
    superior.spa(panel, block, boot["reps"], boot["seed"])
    superior.stepm(panel, fwer, block, boot["reps"], boot["seed"])
    return {
        "scale": int(panel.size),
        "bytes_in": sample.weight([folder / "equity.parquet"]),
    }


def feedquality_detect(cfg: dict) -> sample.Workload:
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


def autopilot_facts(cfg: dict) -> sample.Workload:
    """Every number of one judging step's studies, as the autopilot gathers them before a judge.

    Args:
        cfg: What config.load() returned.

    Returns:
        Fact rows gathered, and bytes of the per-strategy results read.
    """
    project, step = cfg["sample"]["facts"]
    found = facts.gather(project, step)
    read = [
        f
        for study in facts.BY_N[step]["studies"]
        for r in sources.results(project, study)[:1]
        if r["path"].is_dir()
        for f in r["path"].rglob("*")
        if f.suffix in (".json", ".parquet", ".csv")
    ]
    return {"scale": len(found), "bytes_in": sample.weight(read)}


def profilepower_replication(cfg: dict) -> sample.Workload:
    """One planted edge through the profile's own test, on one cell, at a short null.

    Args:
        cfg: What config.load() returned.

    Returns:
        Bars of the cell. 250 draws of the 3,000 a replication can take, on an edge large
        enough never to stop early: the cost is linear in draws and in bars.
    """
    study = power_inputs.config(["run.seed=1", "judge.cut=0.05"])
    study["profile"]["nulls"]["draws"] = 250
    frame = power_inputs.bars("EURUSD", "H4")
    power_one.run(
        ("EURUSD", "H4", "channel55", "long", 50.0, 0),
        frame,
        assetdata.load("EURUSD"),
        study,
    )
    return {"scale": len(frame), "bytes_in": int(frame.memory_usage().sum())}


def pooledprofile_asset(cfg: dict) -> sample.Workload:
    """One asset of a group against the group's joint null, every measure, at a short null.

    Args:
        cfg: What config.load() returned.

    Returns:
        Bars of the asset. 20 draws of the 3,000 the study takes: linear in draws and bars.
    """
    study = pooled_inputs.config(["run.seed=1"])
    study["profile"]["nulls"]["draws"] = 20
    frame = power_inputs.bars("EURUSD", "H4")
    pooled_one.run("EURUSD", "forex", "H4", frame, assetdata.load("EURUSD"), study)
    return {"scale": len(frame), "bytes_in": int(frame.memory_usage().sum())}


def falsepositives_donor(cfg: dict) -> sample.Workload:
    """One donor's monkeys drawn and read by the whole chain, cascade off, at the control's settings.

    Args:
        cfg: What config.load() returned.

    Returns:
        Monkey trades priced and bytes of the harvest read.
    """
    project, databank, _ = cfg["sample"]["gate"]["harvest"]
    gate = cfg["sample"]["gate"]
    got = fp_inputs.load(
        project,
        databank,
        gate["feed"],
        1,
        fp_inputs.judge.CRITERIA,
        harvest_dir(*gate["harvest"]),
    )
    key, own = next(iter(got["real"]["trades"].groupby("identity", observed=True)))
    drawn, _ = fp_model.monkeys(
        own, got["real"]["bars"], got["nullcfg"], fp_inputs.config([])["monkeys"], key
    )
    fp_chain.facts8(fp_chain.as_harvest(drawn, got["real"]), got["gate_cfg"])
    return {
        "scale": len(drawn),
        "bytes_in": sample.weight([Path(got["source"]["harvest"]) / "trades.parquet"]),
    }
