#!/usr/bin/env python3
"""The shape of the strategy a task may generate: how complex, which orders, which exits."""

import re

# Bars are what SQX stores, hours are what the owner reasons in. A 24-bar cap means one
# day on H1 and half a day on M30, so the conversion has to happen per task.
TF_MINUTES = {"M5": 5, "M15": 15, "M30": 30, "H1": 60, "H2": 120, "H4": 240, "D1": 1440}

# One doctrine flag can govern more than one SQX block: a trailing stop is two of them.
EXIT_BLOCKS = {"stop_loss": ["StopLoss.StopLoss"],
               "profit_target": ["ProfitTarget.ProfitTarget"],
               "trailing_stop": ["TrailingStop.TrailingStop", "TrailingStop.TrailingActivation"],
               "move_sl_to_be": ["MoveSL2BE.MoveSL2BE", "MoveSL2BE.SL2BEAddPips"],
               "by_condition": ["_ExitRule_"]}
BARS_BLOCK = "ExitAfterBars.ExitAfterBars"
BLOCKS = re.compile(r"<Blocks\b[^>]*>.*?</Blocks>", re.S)


def block_use(text: str, key: str, use: bool) -> str:
    """Turn one generator block on or off.

    Args:
        text: XML holding <Block key="..."> elements.
        key: The block key, e.g. "TrailingStop.TrailingStop".
        use: Whether the generator may emit it.

    Returns:
        The text with that block's `use` attribute set.
    """
    return re.sub(rf'(<Block key="{re.escape(key)}"[^>]*?)use="[^"]*"',
                  rf'\g<1>use="{str(use).lower()}"', text)


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
    section = re.search(r"<OrderTypes>.*?</OrderTypes>", BLOCKS.search(text).group(0), re.S).group(0)
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
    return max(1, round(b["min_hours"] * per_hour)), max(1, round(b["max_hours"] * per_hour))


def set_exit_types(text: str, exits: dict, timeframe: str) -> tuple[str, int]:
    """Leave only the exits the doctrine allows, and bound the bar exit in hours.

    Args:
        text: A task XML.
        exits: The doctrine's `exits` mapping.
        timeframe: SQX timeframe name, which converts the hour bounds to bars.

    Returns:
        The text and how many exit types stayed enabled — that count is also the cap
        written into maxExitTypes, so the generator cannot ask for more kinds of exit
        than exist. SL and PT are off on purpose: the real stop is decided later, by the
        module that sizes it, once the edge is known to be there.
    """
    whole = BLOCKS.search(text).group(0)
    section = re.search(r"<ExitTypes>.*?</ExitTypes>", whole, re.S).group(0)
    out = block_use(section, BARS_BLOCK, True)
    enabled = 1
    for flag, keys in EXIT_BLOCKS.items():
        for key in keys:
            out = block_use(out, key, bool(exits[flag]))
        enabled += bool(exits[flag])

    lo, hi = bar_range(exits, timeframe)
    bars = re.search(rf'<Block key="{BARS_BLOCK}".*?</Block>', out, re.S).group(0)
    fixed = re.sub(r'<Param key="#ExitAfterBars#"[^>]*/>',
                   '<Param key="#ExitAfterBars#" name="Exit After Bars" type="int" '
                   f'paramType="null" generation="random" minValue="{lo}" maxValue="{hi}" '
                   'step="1" />', bars)
    return text.replace(section, out.replace(bars, fixed, 1), 1), enabled


def set_complexity(text: str, complexity: dict, exit_types: int) -> str:
    """Cap how many conditions a generated strategy may carry, and how far back it may look.

    Args:
        text: A task XML.
        complexity: The doctrine's `complexity` mapping.
        exit_types: How many exit types the task leaves enabled.

    Returns:
        The text with the Main chart's bounds rewritten. The lookback is min and max at
        once: a single shift value is the only way to stop the generator reaching back
        for the bar that happens to fit.
    """
    shift = complexity["lookback_bars"]
    want = {"minConditions": 1, "maxConditions": complexity["max_entry_conditions"],
            "minExitConditions": 1, "maxExitConditions": complexity["max_exit_conditions"],
            "minExitTypes": 1, "maxExitTypes": exit_types,
            "minShift": shift, "maxShift": shift}
    tag = re.search(r'<Chart name="Main chart"[^>]*>', text).group(0)
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
    section = re.search(r"<SLPTOptions>.*?</SLPTOptions>", text, re.S).group(0)
    out = section
    for tag in ("SLRequired", "PTRequired", "SLATR", "PTATR", "SLFixedPips", "PTFixedPips",
                "SLPercent", "PTPercent", "SLIndicatorBased", "PTIndicatorBased",
                "LimitSLPTRRR"):
        out = re.sub(f"<{tag}>[^<]*</{tag}>", f"<{tag}>false</{tag}>", out)
    return text.replace(section, out, 1)
