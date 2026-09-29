"""Every strategy of one export through every rung: the panel the population reading starts from."""

import time

import pandas as pd

from core import fanout
from core.study import blocks, result as envelope
from engines.nulls import simulate
from studies.readings.monkey import one

# What the workers read, set before the pool forks: every market's bars, the config and every
# (strategy, market)'s trades on the sample, each handed over without pickling.
_SHARED: dict = {}


def _one(key: tuple[str, str]) -> dict:
    """One strategy on one market, in a worker that inherited the sample by fork."""
    trades = _SHARED["sample"][key]
    # The feed is what names the asset whose costs the distrust lines check.
    cfg = {**_SHARED["cfg"], "feed": key[1]}
    # Seeded by the strategy alone, as before markets were split: a one-market export
    # draws exactly the monkeys it always drew.
    return one.row(one.measure(trades, _SHARED["frames"][key[1]], cfg, key[0]),
                   len(trades), cfg)


def run(sample: dict[tuple[str, str], pd.DataFrame], frames: dict[str, pd.DataFrame],
        cfg: dict, workers: int) -> dict:
    """Every (strategy, market) with enough trades, one process each, the longest first.

    Args:
        sample: (strategy name, market feed) -> its trades on the sample.
        frames: Market feed -> its bars.
        cfg: What inputs.config() returned.
        workers: Tasks run at once.

    Returns:
        {"population": the export's result, "panel": nulls.csv's frame, one row per strategy
        and market}. This module judges nobody: the population verdict — how many beat
        their monkeys against how many chance gives — is tasks' monkeyExcess, which reads
        this panel.
    """
    started = time.time()
    # Too few trades and there is no p to compute; such a pair never reaches a worker.
    keys = [k for k in sorted(sample) if len(sample[k]) >= cfg["verdict"]["min_trades"]]
    _SHARED.update(sample=sample, frames=frames, cfg=cfg)
    for frame in frames.values():
        simulate.warm(frame, cfg)
    simulate.prime(simulate.fixed(sample[keys[0]], frames[keys[0][1]], cfg), cfg)
    rows = {}
    for i, (key, got) in enumerate(fanout.run(_one, {k: len(sample[k]) for k in keys},
                                              workers), 1):
        rows[key] = got
        envelope.progress(100 * i // len(keys), f"{i}/{len(keys)} {key[0]} · {key[1]}")
    panel = pd.DataFrame([{"strategy": s, "market": m, **rows[s, m]} for s, m in keys])
    panel = panel.set_index("strategy")
    label = (lambda s, m: s) if len(frames) == 1 else (lambda s, m: f"{s} · {m}")
    head, alpha = cfg["nulls"]["headline"], cfg["verdict"]["alpha"]
    shown = panel[[c for c in panel.columns if c.startswith(f"p_{head}_")] + ["n"]]
    population = envelope.envelope(
        one.MODULE, None, None, cfg, started,
        [envelope.tab("panel", "Cada estrategia contra sus monos", [
            {"kind": "bars", "title": f"p en {c[len(f'p_{head}_'):]} — peldaño {head}",
             "unit": "p", "reference": alpha,
             "items": [{"label": label(s, m), "value": float(v), "error": None,
                        "state": "pass" if float(v) <= alpha else "fail"}
                       for s, m, v in zip(panel.index, panel["market"], panel[c])]}
            for c in shown.columns if c != "n"]
            + [blocks.table("Todas", panel.reset_index())],
            note=f"{cfg['nulls']['draws']:,} monos por estrategia, mercado y peldaño, "
                 f"semilla {cfg['nulls']['seed']}. Sin veredicto: cuántas baten a sus monos "
                 f"contra cuántas daría el azar lo dice monkeyExcess, que lee este panel.")])
    return {"population": population, "panel": panel}
