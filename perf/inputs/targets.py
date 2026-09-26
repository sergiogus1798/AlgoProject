"""The registry of everything the catalogue measures: one row is one comparable number."""

from collections.abc import Callable

from perf.inputs import parsers, workloads

# Adding a target is a function in workloads.py or parsers.py and one row here. Nothing
# else changes: the harness, the history and the panel all read this dict. `unit` is what
# `scale` counts, and it is stored with every row so a time can be read per unit of work.
TARGETS: dict[str, dict] = {
    "montecarlo.stream": {"area": "strategies", "unit": "trades",
                          "call": workloads.montecarlo_stream},
    "montecarlo.analyse": {"area": "strategies", "unit": "trades",
                           "call": workloads.montecarlo_analyse},
    "montecarlo.analyse_long": {"area": "strategies", "unit": "trades",
                                "call": workloads.montecarlo_analyse_long},
    "retest.load_sims": {"area": "strategies", "unit": "rows",
                         "call": workloads.retest_load_sims},
    "crossmarket.paired": {"area": "strategies", "unit": "bars",
                           "call": workloads.crossmarket_paired},
    "atrcalculator.reading": {"area": "strategies", "unit": "trades",
                              "call": workloads.atrcalculator_reading},
    "snooping.superior": {"area": "strategies", "unit": "cells",
                          "call": workloads.snooping_superior},
    "feedquality.detect": {"area": "strategies", "unit": "bars",
                           "call": workloads.feedquality_detect},
    "core.trades_read": {"area": "core", "unit": "rows", "call": parsers.trades_read},
    "core.bars_read": {"area": "core", "unit": "bars", "call": parsers.bars_read},
    "core.sqx_xml": {"area": "core", "unit": "files", "call": parsers.sqx_xml},
    "core.sqx_stats": {"area": "core", "unit": "files", "call": parsers.sqx_stats},
}


def resolve(names: list[str] | None) -> dict[str, Callable]:
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
