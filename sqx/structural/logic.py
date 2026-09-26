"""Rewrite a strategy's rules, not its values: drop one entry condition, or flip the order direction."""

import re

# The signals the builder writes, by the <name> of the boolean variable they assign. Only
# the entries are ablated: an exit signal is a different test and none of this corpus has one.
ENTRY_SIGNALS = ("LongEntrySignal", "ShortEntrySignal")
VARIABLE = re.compile(r"<variable\b[^>]*>\s*<id>([^<]*)</id>\s*<name>([^<]*)</name>", re.S)
SIGNAL = re.compile(r'<signal variable="([^"]+)">(.*?)</signal>', re.S)
TOP = re.compile(r'\s*<Item key="(AND|OR)">')
TAG = re.compile(r"<(/?)Block\b[^>]*?(/?)>")
KEY = re.compile(r'<Item\b[^>]*?\bkey="([^"]+)"')
RULES = re.compile(r"<Rules>.*?</Rules>", re.S)
DIRECTION = re.compile(r'(<Param\b[^>]*key="#Direction#"[^>]*>)(-?\d+)(</Param>)')
DIRECTION_ATTR = re.compile(r'\bvalue="(-?\d+)"')
ENTRY_ORDER = re.compile(r'<Item\b[^>]*key="Enter(?:AtMarket|AtStop|AtLimit)"')
# Everything that names a side, and its mirror. One alternation, so a swapped word is never
# swapped back in the same pass.
SIDES = {'Rule name="Long entry"': 'Rule name="Short entry"',
         'Rule name="Long exit"': 'Rule name="Short exit"',
         "MarketPositionIsLong": "MarketPositionIsShort",
         "Market Position Is Long": "Market Position Is Short",
         ') is Long"': ') is Short"'}
SIDES |= {v: k for k, v in SIDES.items()}
SIDE = re.compile("|".join(re.escape(k) for k in SIDES))
# An exit placed at a price level is not mirrored by flipping the order: only strategies
# with no stop, no target and no trailing are inverted. They are all ".None" at step 23.
EXIT_FORMULA = re.compile(r'<Formula key="SQ\.Formulas\.(?:SLPT|RangeLevel|Range)\.(\w+)"')


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
                         "index": k, "block": KEY.search(inner[s:e]).group(1)})
    return rows


def ablate(portfolio: str, signal: str, index: int) -> str:
    """The same strategy with one entry condition deleted.

    In an AND, one term fewer is the condition neutralised; in an OR it is the condition
    forced false. No "always true" block is needed (encargo 12 §1).

    Args:
        portfolio: Text of `strategy_Portfolio.xml`.
        signal: `LongEntrySignal` or `ShortEntrySignal`.
        index: Which direct child of its AND/OR, as `conditions` numbers them.

    Returns:
        The text with that `<Block>…</Block>` gone and nothing else touched. Raises
        ValueError when the operator would be left empty: that is not a filter removed,
        it is a strategy with no entry rule, and SQX's reading of it is unknown.
    """
    vid = _signal_ids(portfolio)[signal]
    match = next(m for m in SIGNAL.finditer(portfolio) if m.group(1) == vid)
    body = match.group(2)
    top = TOP.match(body)
    spans = _top_blocks(body[top.end():]) if top else []
    if len(spans) < 2:
        raise ValueError(f"{signal} has {len(spans)} condition(s) under an AND/OR: "
                         "deleting one would leave no entry rule")
    s, e = spans[index]
    at = match.start(2) + top.end()
    return portfolio[:at + s] + portfolio[at + e:]


def direction(portfolio: str) -> list[int]:
    """The direction every entry order of the strategy places, read back.

    Args:
        portfolio: Text of `strategy_Portfolio.xml`.

    Returns:
        1 (long) or -1 (short) per entry order, in file order.
    """
    rules = RULES.search(portfolio).group(0)
    out = []
    for order in ENTRY_ORDER.finditer(rules):
        out.append(int(DIRECTION.search(rules, order.end()).group(2)))
    return out


def invert(portfolio: str) -> str:
    """The same entry instants with the opposite order direction (encargo 12 §1, D2).

    Every `#Direction#` in the rules changes sign — the entry orders' and the
    ClosePosition's, whose `Any=0` stays 0 — and every word that names a side is swapped:
    the rule names and `MarketPositionIsLong`↔`Short`. The signals and the conditions are
    untouched, so the strategy enters on the very same bars. SQX's `label` attribute is
    left as it is: SQX itself leaves it stale (a short entry it wrote carries `label="Long"`).

    Args:
        portfolio: Text of `strategy_Portfolio.xml`.

    Returns:
        The rewritten text. Raises ValueError when an entry carries a stop, a target, a
        trailing or a break-even: those are placed at a distance the flip would mirror only
        for some formulas, and at step 23 there are none to mirror.
    """
    rules = RULES.search(portfolio)
    text = rules.group(0)
    armed = [f for f in EXIT_FORMULA.findall(text) if f != "None"]
    if armed:
        raise ValueError(f"exit formulas {sorted(set(armed))}: inversion is only a mirror "
                         "without stops, targets or trailing")

    def flip(match: re.Match) -> str:
        """One #Direction# parameter with its value, and its value attribute, negated."""
        head = DIRECTION_ATTR.sub(lambda a: f'value="{-int(a.group(1))}"', match.group(1))
        return f"{head}{-int(match.group(2))}{match.group(3)}"

    text = SIDE.sub(lambda m: SIDES[m.group(0)], DIRECTION.sub(flip, text))
    return portfolio[:rules.start()] + text + portfolio[rules.end():]
