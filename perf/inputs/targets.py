"""The registry of everything the catalogue measures: one row is one comparable number."""

from collections.abc import Callable
from typing import TypedDict

from perf.inputs import construct, gate, parsers, workloads
from perf.inputs.sample import Workload

# Adding a target is a function in workloads.py or parsers.py and one row here. Nothing
# else changes: the harness, the history and the panel all read this dict. `unit` is what
# `scale` counts, and it is stored with every row so a time can be read per unit of work.
class Target(TypedDict):
    """One catalogue row: its area, what `scale` counts, and the function that does the work."""

    area: str
    unit: str
    call: Callable[[dict], Workload]


TARGETS: dict[str, Target] = {
    "montecarlo.stream": {"area": "strategies", "unit": "trades",
                          "call": workloads.montecarlo_stream},
    "montecarlo.analyse": {"area": "strategies", "unit": "trades",
                           "call": workloads.montecarlo_analyse},
    "montecarlo.analyse_long": {"area": "strategies", "unit": "trades",
                                "call": workloads.montecarlo_analyse_long},
    "retest.load_sims": {"area": "strategies", "unit": "rows",
                         "call": workloads.retest_load_sims},
    "snooping.superior": {"area": "strategies", "unit": "cells",
                          "call": workloads.snooping_superior},
    "feedquality.detect": {"area": "strategies", "unit": "bars",
                           "call": workloads.feedquality_detect},
    "autopilot.facts": {"area": "strategies", "unit": "rows", "call": workloads.autopilot_facts},
    "gate.stage": {"area": "gate", "unit": "strategies", "call": gate.gate_stage},
    "gate.level0": {"area": "gate", "unit": "strategies", "call": gate.gate_level0},
    "gate.level1a": {"area": "gate", "unit": "strategies", "call": gate.gate_level1a},
    "gate.level1b": {"area": "gate", "unit": "strategies", "call": gate.gate_level1b},
    "gate.level2": {"area": "gate", "unit": "strategies", "call": gate.gate_level2},
    "gate.level3ab": {"area": "gate", "unit": "strategies", "call": gate.gate_level3ab},
    "gate.monkey": {"area": "gate", "unit": "strategies", "call": gate.gate_monkey},
    "gate.kept": {"area": "gate", "unit": "strategies", "call": gate.kept_rows},
    "falsepositives.donor": {"area": "strategies", "unit": "trades",
                             "call": workloads.falsepositives_donor},
    "profilepower.replication": {"area": "research", "unit": "bars",
                                 "call": workloads.profilepower_replication},
    "pooledprofile.asset": {"area": "research", "unit": "bars",
                            "call": workloads.pooledprofile_asset},
    "portfolio.universe_member": {"area": "portfolio", "unit": "trades",
                                  "call": construct.universe_member},
    "portfolio.close_curve": {"area": "portfolio", "unit": "strategies",
                              "call": construct.close_curve},
    "portfolio.pairs_table": {"area": "portfolio", "unit": "pairs", "call": construct.pairs_table},
    "portfolio.rank_search": {"area": "portfolio", "unit": "combinations",
                              "call": construct.rank_search},
    "portfolio.stage_b": {"area": "portfolio", "unit": "paths", "call": construct.stage_b},
    "portfolio.verdict_null": {"area": "portfolio", "unit": "draws",
                               "call": construct.verdict_null},
    "portfolio.funded_bank": {"area": "portfolio", "unit": "configurations",
                              "call": construct.funded_bank},
    "portfolio.weights_wf": {"area": "portfolio", "unit": "arms", "call": construct.weights_wf},
    "core.trades_read": {"area": "core", "unit": "rows", "call": parsers.trades_read},
    "core.bars_read": {"area": "core", "unit": "bars", "call": parsers.bars_read},
    "core.ticks_read": {"area": "core", "unit": "ticks", "call": parsers.ticks_read},
    "core.sqx_xml": {"area": "core", "unit": "files", "call": parsers.sqx_xml},
    "core.sqx_stats": {"area": "core", "unit": "files", "call": parsers.sqx_stats},
}


def resolve(names: list[str] | None) -> dict[str, Target]:
    """The targets a run covers, by name.

    Args:
        names: Target names or area names, or None for every target.

    Returns:
        Name to entry, in registry order. An area name expands to every target in it, so
        `--only core` and `--only core.sqx_xml` both work.
    """
    if not names:
        return dict(TARGETS)
    return {k: v for k, v in TARGETS.items()
            if k in names or v["area"] in names or k.split(".")[0] in names}
