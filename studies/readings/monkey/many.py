"""Every strategy of one export through every rung: the panel the population reading starts from."""

import time

import pandas as pd

from core import fanout
from core.study import blocks, result as envelope
from engines.nulls import simulate
from studies.readings.monkey import one

# What the workers read, set before the pool forks: the bars, the config and every
# strategy's trades on the sample, each handed over without pickling.
_SHARED: dict = {}


def _one(name: str) -> dict:
    """One strategy's line, in a worker that inherited the sample by fork."""
    trades = _SHARED["sample"][name]
    return one.row(one.measure(trades, _SHARED["frame"], _SHARED["cfg"], name), len(trades),
                   _SHARED["cfg"])


def run(sample: dict[str, pd.DataFrame], frame: pd.DataFrame, cfg: dict,
        workers: int) -> dict:
    """Every strategy with enough trades, one process each, the longest first.

    Args:
        sample: Strategy name -> its trades on the sample.
        frame: The bars.
        cfg: What inputs.config() returned, with `feed` set.
        workers: Strategies run at once.

    Returns:
        {"population": the export's result, "panel": nulls.csv's frame}. This module
        judges nobody: the population verdict — how many beat their monkeys against how
        many chance gives — is tasks' monkeyExcess, which reads this panel.
    """
    started = time.time()
    # Too few trades and there is no p to compute; such a strategy never reaches a worker.
    names = [n for n in sorted(sample) if len(sample[n]) >= cfg["verdict"]["min_trades"]]
    _SHARED.update(sample=sample, frame=frame, cfg=cfg)
    simulate.warm(frame, cfg)
    simulate.prime(simulate.fixed(sample[names[0]], frame, cfg), cfg)
    rows = {}
    for i, (name, got) in enumerate(fanout.run(_one, {n: len(sample[n]) for n in names},
                                               workers), 1):
        rows[name] = got
        envelope.progress(100 * i // len(names), f"{i}/{len(names)} {name}")
    panel = pd.DataFrame(rows).T.loc[names].rename_axis("strategy")
    head, alpha = cfg["nulls"]["headline"], cfg["verdict"]["alpha"]
    shown = panel[[c for c in panel.columns if c.startswith(f"p_{head}_")] + ["n"]]
    population = envelope.envelope(
        one.MODULE, None, None, cfg, started,
        [envelope.tab("panel", "Cada estrategia contra sus monos", [
            {"kind": "bars", "title": f"p en {c[len(f'p_{head}_'):]} — peldaño {head}",
             "unit": "p", "reference": alpha,
             "items": [{"label": s, "value": float(v), "error": None,
                        "state": "pass" if float(v) <= alpha else "fail"}
                       for s, v in panel[c].items()]}
            for c in shown.columns if c != "n"]
            + [blocks.table("Todas", panel.reset_index())],
            note=f"{cfg['nulls']['draws']:,} monos por estrategia y peldaño. Sin veredicto: "
                 f"cuántas baten a sus monos contra cuántas daría el azar lo dice "
                 f"monkeyExcess, que lee este panel.")])
    return {"population": population, "panel": panel}
