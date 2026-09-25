#!/usr/bin/env python3
"""One MC Retest task: the perturbation it runs, the window it re-runs, its acceptance off."""

import re

from core.assetdata import mc_retest
from core.assetdata import window as epoch
from sqx.projects.ranges import RANDOMIZE, set_ranges
from sqx.projects.setups import bounds, set_costs, set_data_range

BLOCK = re.compile(r"<MonteCarloRetest\b.*?</MonteCarloRetest>", re.S)
OUT_OF_SAMPLE = re.compile(r"<OutOfSample\b[^>]*(?:/>|>.*?</OutOfSample>)", re.S)
METHOD = re.compile(r'<Method use="\w+" type="(\w+)">.*?</Method>', re.S)
# Each range method's two bounds come from the asset, so a method whose range the asset
# leaves undecided cannot be written: it would randomise within SQX's factory numbers and
# call the result this instrument's robustness.
FROM_ASSET = {method: name for name, method in RANDOMIZE.items()}
# A fact about the method, not a choice about the study: the minimum distance is how close
# to price a PENDING order may sit before the broker refuses it, so over a population that
# only enters at market it randomises a number nothing reads. Owner's rule, 2026-09-23.
NEEDS_PENDING = ("RandomizeMinDistance",)
# Reserved for the WFC and the WFM. A task here may not name it, in a span or alone.
RESERVED = "oos2"


def usable(spec: dict, data: dict, pending: bool | None) -> tuple[dict, dict]:
    """Which of a task's perturbations can actually run here, and why the rest cannot.

    Args:
        spec: One task of the `mc_retest` catalogue.
        data: One asset as load() returned it.
        pending: Whether the population trades with stop or limit orders. None when the
            build has not run and the question is still open.

    Returns:
        (methods to write, dropped method to its reason). Conditionality belongs to the
        method and not to the task, because the stress task carries six of them: an
        undecided range or a market-only population must cost it that one method, never
        the whole reading. A task left with nothing to perturb is not written at all.
    """
    ranges, keep, dropped = mc_retest(data), {}, {}
    for method, params in spec["methods"].items():
        span = ranges.get(FROM_ASSET[method], {"min": None}) if method in FROM_ASSET else {}
        if method in NEEDS_PENDING and pending is not True:
            dropped[method] = ("la poblacion no lleva ordenes stop ni limit"
                               if pending is False else
                               "sin poblacion construida: el generador PUEDE emitir "
                               "ordenes pendientes, la pregunta sigue abierta")
        elif span.get("min") is None and method in FROM_ASSET:
            dropped[method] = (f"rango {FROM_ASSET[method]} sin decidir en "
                               f"assets/symbols/{data['symbol']}.yaml")
        else:
            keep[method] = params
    return keep, dropped


def set_methods(block: str, methods: dict) -> str:
    """Leave exactly the named perturbations active, with the parameters they are given.

    Args:
        block: The <MonteCarloRetest> element.
        methods: Method type to its parameters. An empty mapping means the method takes
            its two bounds from the asset instead, written afterwards by `set_ranges`.

    Returns:
        The element with every other method switched off. Isolation is the whole design:
        a task that perturbs two things cannot attribute its damage to either, and the
        Python side refuses a databank whose run carried a method it did not expect.
    """
    def one(m: re.Match) -> str:
        """One <Method>, switched on or off and given its parameters when it is on."""
        kind = m.group(1)
        out = m.group(0).replace('<Method use="false"', '<Method use="true"', 1) \
            if kind in methods else m.group(0).replace('<Method use="true"',
                                                       '<Method use="false"', 1)
        for key, value in methods.get(kind, {}).items():
            out = re.sub(rf'(<Param key="{key}"[^>]*>)[^<]*',
                         rf"\g<1>{str(value).lower() if isinstance(value, bool) else value}",
                         out)
        return out
    return METHOD.sub(one, block)


def set_settings(block: str, simulations: int, precision: int, full_sample: bool) -> str:
    """How many times the perturbed backtest runs, at what fidelity, over which sample.

    Args:
        block: The <MonteCarloRetest> element.
        simulations: NumberOfSimulations.
        precision: MCBacktestPrecision — 1 is the task's own timeframe, 2 is one minute.
        full_sample: Whether the simulations cover the whole window or only its in-sample
            part. The Python side reads this attribute to label the run, so it has to say
            what the window actually is.

    Returns:
        The element with the three settings written.
    """
    for tag, value in (("NumberOfSimulations", simulations),
                       ("MCBacktestPrecision", precision),
                       ("MCUseFullSample", str(full_sample).lower())):
        block = re.sub(rf"<{tag}>[^<]*</{tag}>", f"<{tag}>{value}</{tag}>", block)
    return block


def silence(block: str) -> tuple[str, int]:
    """Turn off every acceptance condition of the cross-check.

    Args:
        block: The <MonteCarloRetest> element.

    Returns:
        The element and how many conditions were turned off. Owner's decision,
        2026-09-23: these eight tasks are evidence, not a gate. With the conditions live
        SQX drops what fails, each task chains into the next and all the study can say at
        the end is how many survived — never which perturbation killed which strategy,
        which is the only thing eight isolated tasks exist to answer. The verdict is taken
        in Python (`strategies/retest/`) and applied with `/curate`.
    """
    return re.subn(r'(<Condition\s+)use="true"', r'\g<1>use="false"', block)


def disable(text: str) -> str:
    """Leave a task that is not going to run unable to claim it did.

    Args:
        text: A task XML.

    Returns:
        The task with its MC Retest cross-check switched off. A skipped task is left in
        the project and deactivated, so this is what it carries if anyone reactivates it
        from the GUI: switching the cross-check off too means it would then run a plain
        retest, which the Python side rejects for not carrying the methods its databank
        name promises — instead of a Monte Carlo at whatever ranges the donor shipped.
    """
    return BLOCK.sub(lambda m: m.group(0).replace('<MonteCarloRetest use="true"',
                                                  '<MonteCarloRetest use="false"', 1),
                     text, count=1)


def window(spec: dict, data: dict) -> tuple[str, str, str, tuple | None]:
    """Which segment pays and between which dates this task re-runs.

    Args:
        spec: One task of the `mc_retest` catalogue.
        data: One asset as load() returned it.

    Returns:
        (costs segment, dateFrom, dateTo, out-of-sample range or None). Two forms only:
        `build` is that segment as `_policy.yaml` defines it, and `build..oos1` is ONE
        continuous window from the start of the first to the end of the last, with the last
        one also written as the task's out-of-sample range — which is what makes
        `full_sample` mean anything. A span is priced at the LAST segment's costs: it
        covers both samples and the oos spread is the dearer of the two declared, so it is
        read at the pessimistic price. The master charges its in-sample spread over the
        whole span instead — a deliberate divergence, not an oversight.

    Raises:
        SystemExit: When the segment names `oos2`. It is reserved for the WFC and the WFM
            and every look spends it; a catalogue edit is not the place to decide that.
    """
    named = spec["segment"].split("..")
    if RESERVED in named:
        raise SystemExit(f"{spec['title']}: `segment: {spec['segment']}` toca {RESERVED}, "
                         "que esta reservado al WFC y a la WFM — cada mirada lo gasta. "
                         "Si de verdad hace falta, que lo diga el dueno.")
    if len(named) == 1:
        return (named[0], *bounds(data, named[0]), None)
    first, last = named
    return last, bounds(data, first)[0], bounds(data, last)[1], bounds(data, last)


def write_task(text: str, spec: dict, methods: dict, data: dict,
               simulations: int) -> tuple[str, dict]:
    """Turn one Retest task into the MC Retest task the catalogue describes.

    Args:
        text: A task XML.
        spec: One task of the `mc_retest` catalogue.
        methods: The perturbations to actually run, as `usable()` filtered them.
        data: One asset as load() returned it.
        simulations: How many perturbed backtests each strategy gets.

    Returns:
        The task and what was written. The cross-check is switched on here and not by
        `doctrine.apply_doctrine`, which writes `crosschecks.default: []` into every task
        without a generator and so leaves these eight running a plain retest — present,
        named after a perturbation, perturbing nothing, and silent about it.
    """
    segment, start, end, oos = window(spec, data)
    text, setups = set_costs(text, data, segment)
    text = text.replace(f'dateFrom="{bounds(data, segment)[0]}"', f'dateFrom="{start}"')
    # A span moves the start of the window, and the bars the task loads have to move with
    # it: `set_costs` wrote the last segment's range, which on `build..oos1` is five of the
    # fifteen years the Setup now asks for.
    text, _ = set_data_range(text, data, (epoch(data, spec["segment"].split("..")[0])[0],
                                          epoch(data, segment)[1]))
    found = BLOCK.search(text)
    block = set_methods(found.group(0), methods)
    block = set_settings(block, simulations, spec["precision"], spec["full_sample"])
    block, silenced = silence(block)
    text = text[:found.start()] + block.replace(
        '<MonteCarloRetest use="false"', '<MonteCarloRetest use="true"', 1) + text[found.end():]
    text = OUT_OF_SAMPLE.sub(
        '<OutOfSample showGraph="false" />' if oos is None else
        f'<OutOfSample showGraph="false"><Range dateFrom="{oos[0]}" dateTo="{oos[1]}" />'
        "</OutOfSample>", text, count=1)
    ranges = set_ranges(text, data)
    return ranges.pop("text"), {"segment": segment, "from": start, "to": end,
                                "out_of_sample": oos, "setups": setups,
                                "silenced": silenced, "methods": sorted(methods),
                                "ranges": {k: v for k, v in ranges.items() if v}}
