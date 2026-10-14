#!/usr/bin/env python3
"""The shape of the strategy a task may generate: how complex, which orders, which exits."""

import re
from pathlib import Path

from core.assetdata import doctrine
from core.paths import worker_dir
from sqx.inspect.template_check import blocks, rules
from sqx.projects.buildcensus import kind
from sqx.templates.holes import conditions
from core.xmlget import rx, hit

# Bars are what SQX stores, hours are what the owner reasons in. A 24-bar cap means one
# day on H1 and half a day on M30, so the conversion has to happen per task.
TF_MINUTES = {"M5": 5, "M15": 15, "M30": 30, "H1": 60, "H2": 120, "H4": 240, "D1": 1440}

# One doctrine flag can govern more than one SQX block: a trailing stop is two of them.
EXIT_BLOCKS = {
    "stop_loss": ["StopLoss.StopLoss"],
    "profit_target": ["ProfitTarget.ProfitTarget"],
    "trailing_stop": ["TrailingStop.TrailingStop", "TrailingStop.TrailingActivation"],
    "move_sl_to_be": ["MoveSL2BE.MoveSL2BE", "MoveSL2BE.SL2BEAddPips"],
    "by_condition": ["_ExitRule_"],
}
# SQX asks for each exit type twice: `use` says it is available at all, `probability` how
# often the generator reaches for it. 100 is what makes one compulsory.
ALWAYS, SOMETIMES = "100", "50"
BARS_BLOCK = "ExitAfterBars.ExitAfterBars"
BLOCKS = re.compile(r"<Blocks\b[^>]*>.*?</Blocks>", re.S)
STRATEGY_TYPE = re.compile(r"<StrategyType[^>]*>")


def block_use(text: str, key: str, use: bool, probability: str | None = None) -> str:
    """Turn one generator block on or off, and say how often it is reached for.

    Args:
        text: XML holding <Block key="..."> elements.
        key: The block key, e.g. "TrailingStop.TrailingStop".
        use: Whether the generator may emit it.
        probability: Percentage as SQX writes it; omit to leave it alone.

    Returns:
        The text with that block's attributes set.
    """
    text = re.sub(
        rf'(<Block key="{re.escape(key)}"[^>]*?)use="[^"]*"',
        rf'\g<1>use="{str(use).lower()}"',
        text,
    )
    if probability:
        text = re.sub(
            rf'(<Block key="{re.escape(key)}"[^>]*?)probability="[^"]*"',
            rf'\g<1>probability="{probability}"',
            text,
        )
    return text


def set_order_types(text: str, allowed: list[str]) -> str:
    """Leave exactly the listed entry order types available to the generator.

    Args:
        text: A task XML.
        allowed: Block keys to enable, e.g. ["EnterAtMarket"].

    Returns:
        The text with every other order type switched off. Market-only is the default
        because a stop or limit entry fills at a price the backtest assumes and the
        broker does not owe.
    """
    section = rx(
        r"<OrderTypes>.*?</OrderTypes>", hit(BLOCKS.search(text)).group(0), re.S
    ).group(0)
    out = section
    for key in re.findall(r'<Block key="([^"]*)"[^>]*category="orderTypes"', section):
        out = block_use(out, key, key in allowed)
    return text.replace(section, out, 1)


def bar_range(exits: dict, timeframe: str) -> tuple[int, int]:
    """The hold-time window in bars for one timeframe.

    Args:
        exits: The doctrine's `exits` mapping, whose `bars` is in hours.
        timeframe: SQX timeframe name, e.g. "M30".

    Returns:
        (min, max) bars, never below one bar.
    """
    per_hour = 60 / TF_MINUTES[timeframe]
    b = exits["bars"]
    return max(1, round(b["min_hours"] * per_hour)), max(
        1, round(b["max_hours"] * per_hour)
    )


def set_exit_types(text: str, exits: dict, timeframe: str) -> tuple[str, int]:
    """Leave only the exits the doctrine allows, and bound the bar exit in hours.

    Args:
        text: A task XML.
        exits: The doctrine's `exits` mapping.
        timeframe: SQX timeframe name, which converts the hour bounds to bars.

    Returns:
        The text and how many exit types stayed enabled — that count is also the cap
        written into maxExitTypes, so the generator cannot ask for more kinds of exit
        than exist. The bar exit is compulsory and the rule exit optional unless the owner
        asks for it: every strategy leaves the market on its own, and a rule that happens
        to fire is a bonus. SL and PT are off on purpose — the real stop is decided later,
        by the module that sizes it, once the edge is known to be there.
    """
    whole = hit(BLOCKS.search(text)).group(0)
    section = rx(r"<ExitTypes>.*?</ExitTypes>", whole, re.S).group(0)
    out = block_use(section, BARS_BLOCK, True, ALWAYS)
    enabled = 1
    for flag, keys in EXIT_BLOCKS.items():
        odds = (
            ALWAYS
            if exits["condition_required"] and flag == "by_condition"
            else SOMETIMES
        )
        for key in keys:
            out = block_use(out, key, bool(exits[flag]), odds)
        enabled += bool(exits[flag])

    lo, hi = bar_range(exits, timeframe)
    bars = rx(rf'<Block key="{BARS_BLOCK}".*?</Block>', out, re.S).group(0)
    fixed = re.sub(
        r'<Param key="#ExitAfterBars#"[^>]*/>',
        '<Param key="#ExitAfterBars#" name="Exit After Bars" type="int" '
        f'paramType="null" generation="random" minValue="{lo}" maxValue="{hi}" '
        'step="1" />',
        bars,
    )
    return text.replace(section, out.replace(bars, fixed, 1), 1), enabled


def what_to_build(
    text: str, complexity: dict, exit_required: bool
) -> dict[str, tuple[int, int]]:
    """«What to build» for one Build task: min and max conditions for `entry` and for `exit`.

    Args:
        text: A Build task XML; its <StrategyType> says Simple Strategy or which template.
        complexity: The doctrine's `complexity` mapping.
        exit_required: The doctrine's `exits.condition_required` — a template's exit floor.

    Returns:
        Owner's rule 14 (2026-10-02): at most `max_*_conditions` per side. A Simple Strategy
        counts per strategy, so it gets `complexity.simple` as written. With a template SQX
        applies the range to EACH random hole, on top of what the template fixes, so a side
        gets 0..(cap − fixed). A hole bound to a group is this project's fixed condition and
        is filled by the same range: a side holding one is written 1..1, never 0, which would
        let SQX leave the idea out.
    """
    tag = hit(STRATEGY_TYPE.search(text)).group(0)
    if 'type="template"' not in tag:
        return {side: tuple(complexity["simple"][side]) for side in ("entry", "exit")}
    counted = conditions(Path(rx(r'templateFile="([^"]*)"', tag).group(1)))
    out = {}
    for side, floor in (("entry", 1), ("exit", int(exit_required))):
        c = counted[side]
        hi = max(complexity[f"max_{side}_conditions"] - c["fixed"] - c["bound"], 0)
        out[side] = (1, 1) if c["bound"] else (min(0 if c["fixed"] else floor, hi), hi)
    return out


def clock_fixed(template: Path) -> list[str]:
    """The fixed blocks of a template that read the clock or the calendar (rule 15), sorted."""
    # `kind` only needs the category for a non-clock key, so any known one will do.
    return sorted(
        k for k in blocks(rules(template)) if kind(k, 'category="signals"') == "clock"
    )


def exists(name: str, role: str) -> str | None:
    """Where a live project of this name is (install folder or registry row), else None; a retired row is not live."""
    folder = worker_dir(role) / "user/projects" / name
    if folder.exists():
        return str(folder)
    from sqx.projects import (
        registry,
    )  # here: registry -> rankings -> tasksettings -> this module

    live = next(
        (r for r in registry.rows() if r["name"] == name and not r["retired"]), None
    )
    return f"registry.csv, install {live['install']}" if live else None


def early_gates(
    name: str, role: str, template: Path | None, workflow: bool, timeframe: str
) -> list[str]:
    """Refusals before any work: a live name, a clock block fixed (rule 15), a timeframe crossTF lacks."""
    live = exists(name, role)
    out = (
        [
            f"{name} ya existe ({live}): el builder no reconstruye un proyecto vivo. Elige otro "
            "nombre, o retira el Test_ con sqx.projects.retire."
        ]
        if live
        else []
    )
    known = doctrine()["crosstf"]["timeframes"]
    if workflow and timeframe not in known:
        out.append(
            f"{timeframe}: sin timeframes extra en assets/_build.yaml (crosstf.timeframes): "
            f"un workflow no se puede construir ahí. Conocidos: {', '.join(known)}"
        )
    if template and (clock := clock_fixed(template)):
        out.append(
            f"{template.name}: condiciones fijas que leen el reloj o el calendario "
            f"({', '.join(clock)}): regla 15, ningún bloque de hora o fecha."
        )
    return out


def over_the_cap(template: Path, complexity: dict) -> list[str]:
    """Why a template cannot be built under rule 14, one line per side that breaks it.

    Args:
        template: A template .sqx.
        complexity: The doctrine's `complexity` mapping.

    Returns:
        Empty when it fits. Two free holes on a side is 0..4 conditions whatever the range,
        and fixed conditions plus a hole above the cap leaves the hole nothing to hold.
    """
    out = []
    for side, c in conditions(template).items():
        cap, fixed = complexity[f"max_{side}_conditions"], c["fixed"] + c["bound"]
        if c["free"] > 1:
            out.append(
                f"{template.name}: {c['free']} huecos aleatorios libres en «{side}». Con "
                "dos huecos salen hasta 4 condiciones; una plantilla de solo huecos es "
                "una Simple Strategy (--simple long|short), no una plantilla (regla 14)."
            )
        elif fixed + c["free"] > cap:
            out.append(
                f"{template.name}: {fixed} condiciones fijas + {c['free']} hueco en "
                f"«{side}» pasan del máximo de {cap} (regla 14): con {cap} fijas no "
                "cabe hueco."
            )
    return out


def set_complexity(
    text: str, complexity: dict, exit_types: int, exit_required: bool
) -> str:
    """Cap how many conditions a generated strategy may carry, and how far back it may look.

    Args:
        text: A task XML.
        complexity: The doctrine's `complexity` mapping.
        exit_types: How many exit types the task leaves enabled.
        exit_required: Whether a template's strategies must carry an exit condition. False
            leaves its minExitConditions at zero, which is what makes the rule exit optional
            — the bar exit is what guarantees the position closes.

    Returns:
        The text with the Main chart's bounds rewritten from `what_to_build`. The lookback is
        min and max at once: a single shift value is the only way to stop the generator
        reaching back for the bar that happens to fit.
    """
    shift = complexity["lookback_bars"]
    bounds = what_to_build(text, complexity, exit_required)
    want = {
        "minConditions": bounds["entry"][0],
        "maxConditions": bounds["entry"][1],
        "minExitConditions": bounds["exit"][0],
        "maxExitConditions": bounds["exit"][1],
        "minExitTypes": 1,
        "maxExitTypes": exit_types,
        "minShift": shift,
        "maxShift": shift,
    }
    tag = rx(r'<Chart name="Main chart"[^>]*>', text).group(0)
    new = tag
    for attr, value in want.items():
        new = re.sub(f'{attr}="[^"]*"', f'{attr}="{value}"', new)
    return text.replace(tag, new, 1)


def set_slpt(text: str) -> str:
    """Forbid stop loss and profit target in generation.

    Args:
        text: A task XML.

    Returns:
        The text with every SL/PT switch in <SLPTOptions> off. Required, ATR-based,
        fixed-pip and percent forms are all switched separately, and leaving one on is
        enough to put stops back into the population.
    """
    section = rx(r"<SLPTOptions>.*?</SLPTOptions>", text, re.S).group(0)
    out = section
    for tag in (
        "SLRequired",
        "PTRequired",
        "SLATR",
        "PTATR",
        "SLFixedPips",
        "PTFixedPips",
        "SLPercent",
        "PTPercent",
        "SLIndicatorBased",
        "PTIndicatorBased",
        "LimitSLPTRRR",
    ):
        out = re.sub(f"<{tag}>[^<]*</{tag}>", f"<{tag}>false</{tag}>", out)
    return text.replace(section, out, 1)
