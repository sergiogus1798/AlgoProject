#!/usr/bin/env python3
"""Write one segment's window and costs into a task's <Setup> blocks, which is where they live."""

import re
from datetime import date

from core import assetdata
from core.assetdata import sqx_settings, window

SETUP = re.compile(r"<Setup\b[^>]*>.*?</Setup>", re.S)
SYMBOL = re.compile(r"<Symbol\b[^>]*?>")


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


def span(data: dict, segment: str, reserved_ok: bool = False) -> tuple[str, str, str]:
    """A segment name or a `first..last` span as the window it means and who pays for it.

    Args:
        data: One asset as load() returned it.
        segment: A segment name, e.g. "oos1", or a span with two dots, e.g. "build..oos1" —
            ONE continuous window from the start of the first to the end of the last, the
            same notation the MC Retest catalogue uses.
        reserved_ok: Whether `oos2` is allowed. True only for the WFC and the WFM, which
            are the two studies `_policy.yaml` reserves it for; every other caller leaves
            it False so a catalogue edit cannot spend the segment by accident.

    Returns:
        (dateFrom, dateTo, costs segment). A span is priced at the LAST segment's costs:
        it covers both samples and the oos spread is the dearer of the two declared, so it
        is read at the pessimistic price.

    Raises:
        SystemExit: When the span names `oos2`, `reserved_ok` is False and an autonomous
            agent is asking (`core.assetdata.enforced`); a human is never refused (owner,
            2026-09-28).
    """
    named = segment.split("..")
    if "oos2" in named and not reserved_ok and assetdata.enforced():
        raise SystemExit(f"`{segment}` toca oos2, reservado al WFC y a la WFM — cada mirada "
                         "lo gasta. Si de verdad hace falta, que lo diga el dueno.")
    return (bounds(data, named[0])[0], bounds(data, named[-1])[1], named[-1])


def one_setup(block: str, data: dict, segment: str) -> str:
    """Rewrite a single <Setup> with this asset's declared window and costs.

    Args:
        block: The <Setup>…</Setup> text.
        data: One asset as load() returned it.
        segment: Segment name, which picks the spread and the slippage.

    Returns:
        The rewritten block. The commission method is selected by flipping `use` on the
        <Method> entries rather than by adding one: SQX ships both SizeBased and
        PercentageBased in every Setup and exactly one is in use.
    """
    return write_setup(block, sqx_settings(data, segment), *bounds(data, segment))


def write_setup(block: str, s: dict, a: str, b: str) -> str:
    """Write a window and a set of costs into one <Setup>, whoever priced them.

    Args:
        block: The <Setup>…</Setup> text.
        s: Costs in `core.assetdata.sqx_settings`' shape: defaultSpread, defaultSlippage,
            commission {method, value}, swap {type, long, short, triple_swap_on, rollout_hour}.
        a, b: dateFrom and dateTo as YYYY.MM.DD.

    Returns:
        The rewritten block. `one_setup` prices it from `assets/`; the MT5 bridge prices it
        from a prop firm's own account (`mt5.verify.conditions`).
    """
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


def set_data_range(text: str, data: dict, span: tuple[int, int]) -> tuple[str, int]:
    """Write which bars the task LOADS, which is a different place from which it trades.

    Args:
        text: A task XML.
        data: One asset as load() returned it.
        span: (dateFrom, dateTo) in epoch milliseconds.

    Returns:
        The task and how many <Symbol> entries were rewritten.

    🔬 Measured 2026-09-24 on the frozen donor: in all 15 of its tasks the `<Resources>`
    `<Symbol>` range and the `<Setup>` dates say the same thing, because the GUI keeps them
    in sync. A task whose Setup asks for 2008-2026 while its Symbol still declares the
    donor's 2018-2022 is asking to trade bars it never loaded, and nothing in SQX complains.
    Only this asset's own entries are touched: an additional market keeps its own range.
    """
    def rewrite(m: re.Match) -> str:
        """One <Symbol>, rewritten when it is this asset's feed."""
        if f'name="{data["sqx_symbol"]}"' not in m.group(0):
            return m.group(0)
        one = re.sub(r'dateFrom="\d+"', f'dateFrom="{span[0]}"', m.group(0), count=1)
        return re.sub(r'dateTo="\d+"', f'dateTo="{span[1]}"', one, count=1)

    found = [m for m in SYMBOL.finditer(text) if f'name="{data["sqx_symbol"]}"' in m.group(0)]
    return SYMBOL.sub(rewrite, text), len(found)


def set_costs(text: str, data: dict, segment: str) -> tuple[str, int]:
    """Write the window and costs into every <Setup> of a task that trades this asset.

    Args:
        text: A task XML.
        data: One asset as load() returned it.
        segment: Segment name.

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
        return one_setup(m.group(0), data, segment)

    text, _ = set_data_range(SETUP.sub(rewrite, text), data, window(data, segment))
    return text, done


def set_span(text: str, data: dict, segment: str) -> tuple[str, int]:
    """Write a segment or a `first..last` span as the window a task trades and loads.

    Args:
        text: A task XML.
        data: One asset as load() returned it.
        segment: A segment name or a span, e.g. "build..oos1". `oos2` is refused.

    Returns:
        The task and how many Setups were rewritten, priced at the span's last segment.
    """
    start, _, costs = span(data, segment)
    text, done = set_costs(text, data, costs)
    text = text.replace(f'dateFrom="{bounds(data, costs)[0]}"', f'dateFrom="{start}"')
    first = segment.split("..")[0]
    text, _ = set_data_range(text, data, (window(data, first)[0], window(data, costs)[1]))
    return text, done
