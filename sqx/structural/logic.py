"""Read a strategy's entry conditions and order direction from `strategy_Portfolio.xml`."""

import re
from core.xmlget import hit

# The signals the builder writes, by the <name> of the boolean variable they assign. Only
# the entries are read: none of this corpus has an exit signal.
ENTRY_SIGNALS = ("LongEntrySignal", "ShortEntrySignal")
VARIABLE = re.compile(r"<variable\b[^>]*>\s*<id>([^<]*)</id>\s*<name>([^<]*)</name>", re.S)
SIGNAL = re.compile(r'<signal variable="([^"]+)">(.*?)</signal>', re.S)
TOP = re.compile(r'\s*<Item key="(AND|OR)"[^>]*>')
TAG = re.compile(r"<(/?)Block\b[^>]*?(/?)>")
KEY = re.compile(r'<Item\b[^>]*?\bkey="([^"]+)"')
RULES = re.compile(r"<Rules>.*?</Rules>", re.S)
DIRECTION = re.compile(r'(<Param\b[^>]*key="#Direction#"[^>]*>)(-?\d+)(</Param>)')
ENTRY_ORDER = re.compile(r'<Item\b[^>]*key="Enter(?:AtMarket|AtStop|AtLimit)"')


def _signal_ids(portfolio: str) -> dict[str, str]:
    """Entry signal name to the variable id its `<signal>` element carries."""
    return {name: vid for vid, name in VARIABLE.findall(portfolio) if name in ENTRY_SIGNALS}


def _top_blocks(body: str) -> list[tuple[int, int]]:
    """The spans of the direct children of a signal's AND/OR, nested blocks skipped.

    Args:
        body: The text between `<signal …>` and `</signal>`.

    Returns:
        (start, end) per top-level `<Block>…</Block>`, start at the beginning of its line so
        deleting the span leaves the indentation of its neighbours intact.
    """
    spans, depth, start = [], 0, 0
    for tag in TAG.finditer(body):
        closing, selfclosing = tag.group(1), tag.group(2)
        if selfclosing:
            continue
        if not closing:
            if depth == 0:
                start = body.rfind("\n", 0, tag.start()) + 1
            depth += 1
            continue
        depth -= 1
        if depth == 0:
            end = body.find("\n", tag.end())
            spans.append((start, end + 1 if end >= 0 else tag.end()))
    return spans


def conditions(portfolio: str) -> list[dict]:
    """Every entry condition a strategy has, as its signal's direct children.

    Args:
        portfolio: Text of `strategy_Portfolio.xml`.

    Returns:
        One row per condition: `signal` (LongEntrySignal…), `operator` (AND or OR),
        `index` in that operator, and `block`, the key of the condition's outer item —
        `MABarClosesAbove`, or `IsGreater` for a comparison whose operands are nested.
        An empty signal contributes nothing. A signal whose top is not an AND/OR holds a
        single condition and is reported with operator "".
    """
    rows, ids = [], _signal_ids(portfolio)
    for vid, body in SIGNAL.findall(portfolio):
        name = next((n for n, i in ids.items() if i == vid), None)
        if name is None:
            continue
        top = TOP.match(body)
        inner = body[top.end():] if top else body
        for k, (s, e) in enumerate(_top_blocks(inner) if top else [(0, len(body))]):
            rows.append({"signal": name, "operator": top.group(1) if top else "",
                         "index": k, "block": hit(KEY.search(inner[s:e])).group(1)})
    return rows


def direction(portfolio: str) -> list[int]:
    """The direction every entry order of the strategy places, read back.

    Args:
        portfolio: Text of `strategy_Portfolio.xml`.

    Returns:
        1 (long) or -1 (short) per entry order, in file order.
    """
    rules = hit(RULES.search(portfolio)).group(0)
    out = []
    for order in ENTRY_ORDER.finditer(rules):
        out.append(int(hit(DIRECTION.search(rules, order.end())).group(2)))
    return out
