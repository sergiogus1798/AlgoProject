"""What a button actually runs: one strategy analysed, one test repeated, one report written."""

from datetime import date

from strategies.monteCarlo import (config, engine, fan, run, scoring, stability,
                                   strategypage, stream, stress, sweeps)
from core.paths import report_dir
from strategies.monteCarlo.explorer import cache

FAN_SIMS = 2000   # paths behind the equity cone; a picture of the spread, not a gate


def stream_of(setup: dict, name: str) -> dict:
    """One strategy's trade stream, read fresh from the export.

    Args:
        setup: What serve.main() assembled: config, asset, export folder.
        name: Strategy name, the CSV's stem.

    Returns:
        What stream.build() returned. Reading the CSV again costs milliseconds and removes
        every question about what is held in memory between clicks.
    """
    return stream.build(setup["trades"] / f"{name}.csv", setup["asset"],
                        setup["cfg"]["global"]["risk_per_trade"])


def analyse(setup: dict, name: str) -> dict:
    """The whole analysis of one strategy, stored where the panel will find it again.

    Args:
        setup: What serve.main() assembled.
        name: Strategy name.

    Returns:
        A short summary for the panel's log line; everything else goes to the cache.
    """
    cfg, source = setup["cfg"], stream_of(setup, name)
    result = run.analyse(source, setup["day"], setup["asset"], cfg)
    verdict = scoring.verdict(result, cfg)
    band = fan.envelope(source["pnl"], "stationary",
                        config.stationary_block(source["pnl"].size), FAN_SIMS,
                        cfg["global"]["starting_equity"], [5, 25, 50, 75, 95])
    cache.save(setup["project"], setup["databank"], name,
               {"result": result, "verdict": verdict, "band": band}, cfg, setup["asset"])
    return {"strategy": name, "tier": verdict["tier"], "composite": verdict["composite"]}


def band_for(setup: dict, source: dict, label: str) -> dict:
    """The equity cone of one sub-test, computed on demand for the test explorer.

    Args:
        setup: What serve.main() assembled.
        source: What stream_of() returned for this strategy.
        label: A label from sections.runs() — a reordering, a resampling or a stress test.

    Returns:
        What fan.envelope() or fan.stress_envelope() returns, whichever the label's own
        model needs. Cheap enough to redo on every click: FAN_SIMS, not the full n_sims.
    """
    cfg = setup["cfg"]
    steps = {s["label"]: s for s in sweeps.plan(len(source["pnl"]), cfg)}
    model = steps[label]["model"] if label in steps else label
    qs = [5, 25, 50, 75, 95]
    if model in stress.STRESS:
        return fan.stress_envelope(engine.payload(source), model, FAN_SIMS, cfg, qs)
    block = steps[label]["block"] if label in steps else cfg["blocks"]["block_min"]
    return fan.envelope(source["pnl"], model, block, FAN_SIMS,
                        cfg["global"]["starting_equity"], qs)


def report(setup: dict, name: str) -> dict:
    """Write one strategy's report file, stability check included.

    Args:
        setup: What serve.main() assembled.
        name: Strategy name.

    Returns:
        Where the file landed. It is the same page the command writes, from the same
        renderer — but in `montecarlo_panel/`, never in the batch run's own folder: the
        panel is often run at fewer simulations, and a page written under one configuration
        must not silently replace one written under another.
    """
    record = cache.load(setup["project"], setup["databank"], name, setup["cfg"],
                        setup["asset"])
    body = record["body"]
    shared = {**setup["shared"], "vol_model": setup["cfg"]["family_d"]["vol_model"],
              "stability": stability.spread(stream_of(setup, name), setup["cfg"])}
    out = report_dir(setup["project"], setup["databank"],
                     date.today().isoformat()) / "montecarlo_panel"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{name}.html"
    path.write_text(strategypage.page(body["result"], body["verdict"], body["band"],
                                      setup["cfg"], shared), encoding="utf-8")
    return {"path": str(path)}
