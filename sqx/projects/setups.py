#!/usr/bin/env python3
"""Write one segment's window and costs into a task's <Setup> blocks, which is where they live."""

import re
from datetime import date

from core.assetdata import sqx_settings

SETUP = re.compile(r"<Setup\b[^>]*>.*?</Setup>", re.S)


def bounds(data: dict, segment: str) -> tuple[str, str]:
    """One segment as the two dates a <Setup> carries.

    Args:
        data: One asset as load() returned it.
        segment: Segment name.

    Returns:
        (dateFrom, dateTo) as YYYY.MM.DD, both inclusive. A <Setup> writes plain dates,
        not the epoch milliseconds the <Resources> <Symbol> uses for the data range.
    """
    seg = data["segments"][segment]
    at = lambda b, end: (date(b, 12, 31) if end else date(b, 1, 1)) if isinstance(b, int) else b
    return (f"{at(seg['from'], False):%Y.%m.%d}", f"{at(seg['to'], True):%Y.%m.%d}")


def one_setup(block: str, data: dict, segment: str, since: str | None = None) -> str:
    """Rewrite a single <Setup> with this asset's declared window and costs.

    Args:
        block: The <Setup>…</Setup> text.
        data: One asset as load() returned it.
        segment: Segment name, which picks the spread and the slippage.
        since: Override for dateFrom, so a retest can start where the build started.

    Returns:
        The rewritten block. The commission method is selected by flipping `use` on the
        <Method> entries rather than by adding one: SQX ships both SizeBased and
        PercentageBased in every Setup and exactly one is in use.
    """
    s = sqx_settings(data, segment)
    a, b = bounds(data, segment)
    a = since or a
    block = re.sub(r'dateFrom="[^"]*"', f'dateFrom="{a}"', block, count=1)
    block = re.sub(r'dateTo="[^"]*"', f'dateTo="{b}"', block, count=1)
    block = re.sub(r'(<Setup\b[^>]*?)slippage="[^"]*"', rf'\g<1>slippage="{s["defaultSlippage"]}"',
                   block, count=1)
    block = re.sub(r'(<Chart\b[^>]*?)spread="[^"]*"', rf'\g<1>spread="{s["defaultSpread"]}"', block)

    want = s["commission"]["method"]
    block = re.sub(r'(<Method type="(\w+)"[^>]*?)use="[^"]*"',
                   lambda m: f'{m.group(1)}use="{"true" if m.group(2) == want else "false"}"', block)
    block = re.sub(rf'(<Param key="\w+" className="{want}">)[^<]*',
                   rf'\g<1>{s["commission"]["value"]}', block)

    sw = s["swap"]
    block = re.sub(r'<Swap\b[^>]*/>',
                   f'<Swap use="true" type="{sw["type"]}" long="{sw["long"]}" '
                   f'short="{sw["short"]}" tripleSwapOn="{sw["triple_swap_on"]}" '
                   f'rolloutHour="{sw["rollout_hour"]}" />', block)
    return block


def set_oos_range(text: str, start: str, end: str) -> int:
    """Mark which part of a task's tested window is out of sample.

    Args:
        text: A task XML.
        start, end: The OOS bounds as YYYY.MM.DD.

    Returns:
        The text and whether the marker was written. <OutOfSample> lives under <Data>,
        beside <Setups> and not inside a <Setup>, and SQX writes it self-closing when no
        range is set. Without it the retest reports one undifferentiated number over
        fifteen years and the only question worth asking — did it hold up after 2018 —
        has no answer in the result.
    """
    marker = f'<Range dateFrom="{start}" dateTo="{end}" />'
    return re.subn(r"<OutOfSample([^>]*?)/>|<OutOfSample([^>]*?)>.*?</OutOfSample>",
                   lambda m: f"<OutOfSample{(m.group(1) or m.group(2)).rstrip()}>{marker}</OutOfSample>",
                   text, count=1, flags=re.S)


def set_costs(text: str, data: dict, segment: str, since: str | None = None) -> tuple[str, int]:
    """Write the window and costs into every <Setup> of a task that trades this asset.

    Args:
        text: A task XML.
        data: One asset as load() returned it.
        segment: Segment name.
        since: Override for dateFrom, so a retest can start where the build started.

    Returns:
        The task and how many Setups were rewritten.

    A <Setup> is the per-task cost configuration — dates, slippage, the <Chart>'s spread,
    the commission method and the swap — and it is what the GUI edits when a task is given
    its own costs. The <InstrumentInfo> under <Resources> is a different thing: the
    instrument DEFINITION, which must agree with SQX's own registry, and editing it is
    what produces "Project has unresolved resources". Setups carrying another asset's
    chart are left alone, so a cross-check on a second market keeps its own costs.
    """
    feed = f'<Chart symbol="{data["sqx_symbol"]}"'
    done = 0

    def rewrite(m: re.Match) -> str:
        """One Setup, rewritten when it trades this asset and left alone when it does not."""
        nonlocal done
        if feed not in m.group(0):
            return m.group(0)
        done += 1
        return one_setup(m.group(0), data, segment, since)

    return SETUP.sub(rewrite, text), done
