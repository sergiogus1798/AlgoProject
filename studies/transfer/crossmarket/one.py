"""One strategy across every market, returned as the contract's data: what the window paints."""

import time

from core.study import result as envelope
from core.symbols import alias
from studies.transfer.crossmarket import many
from studies.transfer.crossmarket.contract import tabs

MODULE = "studies.transfer.crossmarket"


def run(name: str, inputs: dict, cfg: dict, only: str | None = None,
        overrides: list[str] | None = None) -> dict:
    """Everything the study measures for one strategy.

    The joint random runs belong to the whole export (one draw moves every market and every
    strategy alike), so this measures the export and slices the strategy: no cheaper, no different.

    Args:
        name: Strategy name, exactly as SQX has it.
        inputs: What load.load() returned.
        cfg: What config.load(overrides) returned.
        only: One market feed to show on its own; the other tabs stay whole.
        overrides: The same `--set` values cfg was loaded with.

    Returns:
        The contract dict: the numbers, the markets and the yearly edge; no verdict.
    """
    started = time.time()
    got = many.measure(inputs, overrides)
    mine = got["verdict"][got["verdict"]["strategy"] == name]
    if mine.empty:
        raise ValueError(f"{name}: no es una estrategia del export")
    row = mine.iloc[0]
    markets = got["markets"][got["markets"]["strategy"] == name]
    ident = inputs["identity"].get(name)
    warn = tabs.warnings(markets, ident)
    if only:
        markets = markets[markets["market"] == only]
        warn.append({"code": "parcial", "state": "info",
                     "text": f"Sólo se enseña {alias(only)}; la z conjunta sale de todos los "
                             f"mercados a la vez."})
    return envelope.envelope(
        MODULE, name, ident, cfg, started,
        tabs.strategy_tabs(row, markets, got["d_y"].get(name, []), cfg), None, warn, tabs.GLOSSARY,
        summary={"verdict": many.WORD, **{k: v for k, v in row.items()
                                          if isinstance(v, (int, float)) and k != "strategy"}})
