"""One strategy through every family, returned as the contract's data: what the window paints."""

import time

from core.study import result as envelope
from strategies.monteCarlo import run as study
from strategies.monteCarlo.contract import explorer, headline, order, regime
from strategies.monteCarlo.inputs import config
from strategies.monteCarlo.model import stress
from strategies.monteCarlo.simulate import engine, fan, sweeps
from strategies.monteCarlo.verdict import scoring

MODULE = "strategies.monteCarlo"
FAN_SIMS = 2000   # paths behind an equity cone; a picture of the spread, not a gate
CONE = [2.5, 25, 50, 75, 97.5]


def _progress(done: int, total: int, title: str) -> None:
    """What engine.PROGRESS calls on every batch: the line the window moves its bar with."""
    envelope.progress(100 * done // max(total, 1), title)


def cone(source: dict, label: str, cfg: dict) -> dict:
    """The equity cone of one sub-test under its own model.

    Args:
        source: What stream.build() returned.
        label: A sweep label, or a Family C stress name.
        cfg: What config.load() returned.

    Returns:
        What fan.envelope() or fan.stress_envelope() returns, at the contract's percentiles.
    """
    steps = {s["label"]: s for s in sweeps.plan(len(source["pnl"]), cfg)}
    model = steps[label]["model"] if label in steps else label
    if model in stress.STRESS:
        return fan.stress_envelope(engine.payload(source), model, FAN_SIMS, cfg, CONE)
    block = steps[label]["block"] if label in steps else cfg["blocks"]["block_min"]
    return fan.envelope(source["pnl"], model, block, FAN_SIMS,
                        cfg["global"]["starting_equity"], CONE)


def _rerun(strategy: str, inputs: dict, cfg: dict, only: str, started: float) -> dict:
    """One sub-test again, alone, as a partial result the daemon lays beside the stored one."""
    source = inputs["streams"][strategy]
    steps = {s["label"]: s for s in sweeps.plan(len(source["pnl"]), cfg)}
    step = steps.get(only) or {"label": only, "model": only, "block": 0,
                               "title": stress.TITLES[only]}
    got = study.one(source, step, cfg)
    body = explorer.pair(only, got["title"], got["shapes"], got["table"], rerun=True)
    return envelope.envelope(MODULE, strategy, inputs["identity"].get(strategy), cfg, started,
                             [envelope.tab("explorer", "Explorador de pruebas", body)])


def run(strategy: str, inputs: dict, cfg: dict, only: str | None = None) -> dict:
    """Everything the study says about one strategy.

    Args:
        strategy: Its name in the export.
        inputs: What load.load() returned.
        cfg: What config.load() returned.
        only: A sub-test label (explorer.runs()) to re-run on its own; the result then holds
            that sub-test alone and no verdict, because a verdict comes from a whole
            analysis or from none.

    Returns:
        The contract dict: verdict, seven tabs, warnings, glossary and the summary row.
    """
    started = time.time()
    if not engine.SERIAL:
        # A whole-databank run forks one process per strategy; only a lone run reports
        # each batch, or 96 workers would drown the log.
        engine.PROGRESS = _progress
    if only:
        return _rerun(strategy, inputs, cfg, only, started)
    source = inputs["streams"][strategy]
    result = study.analyse(source, inputs["day"], inputs["asset"], cfg)
    verdict = scoring.verdict(result, cfg)
    cones = {label: cone(source, label, cfg) for label, *_ in explorer.runs(result)}
    tabs = [headline.tab(result, verdict, cfg),
            order.family_a(result, verdict, cones[config.HEADLINE], cfg),
            order.family_b(result, verdict, cfg), regime.family_c(result, verdict, cfg),
            regime.family_d(result, verdict, cfg), regime.family_e(result, verdict, cfg),
            explorer.tab(result, cones), explorer.method(result, cfg, inputs["shared"])]
    warnings = []
    if result["overlap"] > 0.01:
        warnings.append({"code": "solapadas", "state": "watch",
                         "text": f"El {result['overlap']:.0%} de las operaciones estaban "
                                 f"abiertas a la vez que la anterior: la curva sumada vale, "
                                 f"pero las rachas y el orden significan otra cosa."})
    if result["cost_check"]["diverges"]:
        warnings.append({"code": "coste", "state": "watch",
                         "text": f"El coste modelado es {result['cost_check']['ratio']:.2f} "
                                 f"veces el que SQX cobró: la familia C se lee con reserva."})
    return envelope.envelope(MODULE, strategy, inputs["identity"].get(strategy), cfg, started,
                             tabs, headline.verdict_block(result, verdict), warnings,
                             explorer.GLOSSARY, headline.summary(result, verdict))
