#!/usr/bin/env python3
"""Count what a project's Build task will generate from: its shape, its blocks, its search and its acceptance."""

import html
import re
import zipfile
from pathlib import Path

from sqx.projects.patch import NO_TEMPLATE
from sqx.templates.holes import conditions

# Rule 15 (owner, 2026-10-02): nothing that reads the clock or the calendar. Every such block
# the builder can sample is a native of SQX's «Bar And Time» category under one of these names.
CLOCK = re.compile(r"^(Current|Bar)(Hour|Minute|DayOf|WeekOf|Month|Time)|^IsMonth")
# Custom blocks that read the session or the clock, forbidden like the natives (owner, 2026-10-11; SessionClose and the custom-hours volume profiles, 2026-10-13).
CLOCK_NAMES = frozenset({"CBlock_TimeBreakoutLong", "CBlock_TimeBreakoutLong_2",
                         "SessionHigh", "SessionLow", "SessionOpen", "SessionClose",
                         "VolumeProfileCustomHours", "VolumeProfileCustomHoursMultiSession"})
# The Build's own `category` per block → what it is to a strategy. `stopLimitBlocks` is the
# price of a stop or limit ENTRY order; whether such an order can be placed at all is
# `<OrderTypes>` (`EnterAtStop`, `EnterAtLimit`), which `buildrules.set_order_types` governs.
KINDS = {"signals": "condition", "indicators": "value", "stopLimitBlocks": "level"}
BLOCK = re.compile(r'<Block key="([^"]+)" weight="\d+" use="(true|false)"([^>]*)>')
TYPED = re.compile(r'<Block key="([^"]+)"[^>]*?use="(true|false)"(?: probability="(\d+)")?')
CONDITION = re.compile(r'<Condition use="(true|false)">.*?column="([^"]*)".*?sampleType="(\d+)"'
                       r'.*?<Comparator value="([^"]*)".*?<Numeric-Value value="([^"]*)"', re.S)


def kind(key: str, attrs: str) -> str:
    """What one `<BuildingBlocks>` entry is: `condition`, `value`, `level` or `clock`.

    Args:
        key: The block's key as the task writes it, role prefix included.
        attrs: The rest of its opening tag, which holds `category=`.

    Returns:
        `clock` wins over the category: a clock block is one whether it is a condition
        (`BarHourIs`) or a value (`CurrentHour`).
    """
    name = key.rsplit(".", 1)[-1]
    if CLOCK.match(name) or name in CLOCK_NAMES:
        return "clock"
    return KINDS[re.search(r'category="([^"]*)"', attrs).group(1)]


def _section(text: str, tag: str) -> str:
    """The last `<tag>…</tag>` of a task — the one under `<Blocks>`, past `<PartsToImprove>`."""
    return re.findall(rf"<{tag}\b[^>]*>.*?</{tag}>", text, re.S)[-1]


def census(cfx: Path) -> dict:
    """Everything the study must count on a population before it is built, read off the file.

    Args:
        cfx: An installed project.cfx; read only, so a running install may hold it.

    Returns:
        For the project's Build task: `strategy_type` and `template` (with the template's own
        fixed, bound and free conditions per side), `sides` (the `<MarketSides>` switch),
        `entry` and `exit` (min, max conditions of «What to build»), `order_types` and
        `exit_types` switched on, `blocks` (on / of, by `kind`) and `on` (the keys, by kind),
        `generation`, `genetic` (every scalar of `<BuildMode>`), `fitness`, `acceptance`
        (the active `<Rankings>` conditions), `mc_manipulation` (must read false: the cross-check is never used, owner 2026-10-11), and the caps.
    """
    with zipfile.ZipFile(cfx) as z:
        member = next(n for n in z.namelist() if n.startswith("Build-"))
        text = z.read(member).decode("utf-8")
    tag = re.search(r"<StrategyType[^>]*>", text).group(0)
    template = re.search(r'templateFile="([^"]*)"', tag).group(1)
    templated = 'type="template"' in tag
    chart = re.search(r'<Chart name="Main chart"[^>]*>', text).group(0)
    bound = {a: int(v) for a, v in re.findall(r'(\w+)="(\d+)"', chart)}
    blocks = {k: {"on": 0, "of": 0} for k in ("condition", "value", "level", "clock")}
    on = {k: [] for k in blocks}
    for key, use, attrs in BLOCK.findall(_section(text, "BuildingBlocks")):
        k = kind(key, attrs)
        blocks[k]["of"] += 1
        if use == "true":
            blocks[k]["on"] += 1
            on[k].append(key)
    mode = re.search(r"<BuildMode\b.*?</BuildMode>", text, re.S).group(0)
    rankings = re.search(r"<Rankings\b.*?</Rankings>", text, re.S).group(0)
    stop = re.search(r"<StopCondition[^>]*>", rankings).group(0)
    genetic = dict(re.findall(r"<(\w+)>([^<]*)</\1>", mode))
    genetic["InitialPopulationConditions"] = len(re.findall(r"<Condition\b", mode))
    for name, attrs in re.findall(r"<(EvoRestart\w+|EvoInSamplePeriod) ([^>]*?) ?/>", mode):
        genetic[name] = attrs.replace('"', "")
    return {
        "task": member,
        "strategy_type": "template" if templated else "simple",
        "template": template if templated else None,
        "template_conditions": conditions(Path(template)) if templated else None,
        "no_template_named": templated or template == NO_TEMPLATE,
        "sides": re.search(r'<MarketSides type="([^"]*)"', text).group(1),
        "symmetry": dict(re.findall(r"<(EntrySymmetry|ExitSymmetry)>([^<]*)<", text)),
        "entry": [bound["minConditions"], bound["maxConditions"]],
        "exit": [bound["minExitConditions"], bound["maxExitConditions"]],
        "lookback": [bound["minShift"], bound["maxShift"]],
        "order_types": [k for k, use, _ in TYPED.findall(_section(text, "OrderTypes"))
                        if use == "true"],
        "exit_types": {k: int(p) for k, use, p in TYPED.findall(_section(text, "ExitTypes"))
                       if use == "true"},
        "blocks": blocks, "on": on,
        "generation": re.search(r'generationType="([^"]*)"', mode).group(1),
        "genetic": genetic,
        "fitness": re.search(r'<Ranking type="([^"]*)"', rankings).group(1),
        "acceptance": [f"{col} {html.unescape(op)} {value} @sampleType {sample}"
                       for use, col, sample, op, value in CONDITION.findall(rankings)
                       if use == "true"],
        "mc_manipulation": re.search(r'<MonteCarloManipulation use="([^"]*)"', text).group(1),
        "max_strategies": int(re.search(r"<MaxStrategies>(\d+)<", rankings).group(1)),
        "stop": dict(re.findall(r'(\w+)="([^"]*)"', stop)),
    }


def lines(c: dict) -> list[str]:
    """A census as the lines a person reads.

    Args:
        c: A census().

    Returns:
        One line per fact, the condition keys last because they are the long one.
    """
    g, b = c["genetic"], c["blocks"]
    shape = c["strategy_type"] + (f" {c['template']} {c['template_conditions']}"
                                  if c["template"] else " (sin plantilla)")
    return [
        f"{c['task']}: {shape}" + ("" if c["no_template_named"] else "  ⚠️ nombra una plantilla"),
        f"  dirección      {c['sides']}  (simetría entrada {c['symmetry']['EntrySymmetry']}, "
        f"salida {c['symmetry']['ExitSymmetry']})",
        f"  condiciones    entrada {c['entry'][0]}..{c['entry'][1]} · salida "
        f"{c['exit'][0]}..{c['exit'][1]} · lookback {c['lookback'][0]}..{c['lookback'][1]}",
        f"  órdenes        {', '.join(c['order_types'])}",
        "  salidas        " + ", ".join(f"{k} ({p} %)" for k, p in c["exit_types"].items()),
        "  bloques ON     " + " · ".join(
            f"{name} {b[k]['on']}/{b[k]['of']}" for k, name in (
                ("condition", "condiciones"), ("value", "indicadores/valores"),
                ("level", "niveles stop/limit"), ("clock", "reloj/calendario"))),
        f"  generación     {c['generation']} · fitness {c['fitness']}",
        f"  genética       población {g['PopulationSize']} × {g['Islands']} islas · "
        f"generaciones {g['MaxGenerations']} · cruce {g['CrossoverProbability']} · mutación "
        f"{g['MutationProbability']} · migración cada {g['MigrationModulo']} al "
        f"{g['MigrationRate']} % · sangre nueva {g['FreshBloodWeakestPct']} % cada "
        f"{g['FreshBloodWeakestGenerations']} · reinicio al acabar "
        f"[{g['EvoRestartOnFinish']}] y por estancamiento [{g['EvoRestartOnStagnation']}] · "
        f"condiciones de población inicial {g['InitialPopulationConditions']}",
        f"  aceptación     {' & '.join(c['acceptance']) or 'ninguna'} · MC manipulation "
        f"{c['mc_manipulation']}",
        f"  topes          MaxStrategies {c['max_strategies']} · stop {c['stop']}",
        f"  condiciones ON ({b['condition']['on']}): {', '.join(c['on']['condition'])}",
    ] + [f"  {name} ON ({b[k]['on']}): {', '.join(c['on'][k])}"
         for k, name in (("value", "valores"), ("level", "niveles"), ("clock", "reloj"))
         if c["on"][k]]
