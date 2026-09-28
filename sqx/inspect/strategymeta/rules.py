"""What a strategy's rules say, off strategy_Portfolio.xml: its conditions and its entry orders."""

from xml.etree import ElementTree

from sqx.structural import logic

# Parameters that say where or under which id a block runs, not what it tests.
PLUMBING = {"#Identification#", "#Symbol#", "#MagicNumber#", "#Comment#"}
EXIT_METHODS = {"stop_loss": "#StopLoss.StopLoss#", "profit_target": "#ProfitTarget.ProfitTarget#",
                "trailing_stop": "#TrailingStop.TrailingStop#",
                "break_even": "#MoveSL2BE.MoveSL2BE#"}
SIDE = {1: "long", -1: "short"}


def values(root: ElementTree.Element) -> dict[str, str]:
    """Every strategy variable's id to the value it holds.

    Args:
        root: Parsed strategy_Portfolio.xml.

    Returns:
        E.g. {"StopLossCoef1": "9.2"}. A block parameter marked `variable="true"` stores the
        variable's id as its text, never the number: without this map every tuned parameter
        reads as a name.
    """
    return {v.findtext("id"): v.findtext("value") for v in root.iter("variable")}


def _value(param: ElementTree.Element, held: dict[str, str]) -> str:
    """One parameter's value, with a variable reference replaced by what the variable holds."""
    text = (param.text or "").strip()
    return held.get(text, text) if param.get("variable") == "true" else text


def params(item: ElementTree.Element, held: dict[str, str]) -> dict[str, str]:
    """A block's parameters by name, `#` stripped, a nested operand rendered in place.

    Args:
        item: An `<Item>` of the rule tree.
        held: values().

    Returns:
        E.g. {"Indicator": "Stochastic(KPeriod=14, …)", "Bars": "2"}. The chart index and the
        order plumbing (magic number, symbol, comment, identification) are left out.
    """
    out = {}
    for child in item:
        key = child.get("key") or ""
        if child.tag == "Block":
            out[key.strip("#")] = render(child.find("Item"), held)
        elif child.tag == "Param" and key not in PLUMBING and not key.startswith("#Chart"):
            out[key.strip("#")] = _value(child, held)
    return out


def terms(item: ElementTree.Element) -> list[ElementTree.Element]:
    """The operands of an AND/OR, in either layout SQX writes.

    A template's AND wraps each term in a `<Block>`; the generic builder's AND carries
    `generated`/`randomId` attributes and holds its terms as bare `<Item>`s.
    """
    return [c.find("Item") if c.tag == "Block" else c for c in item if c.tag in ("Block", "Item")]


def render(item: ElementTree.Element, held: dict[str, str]) -> str:
    """A block as one readable line: `Key(Param=value, …)`, nested operands inside."""
    if item.get("key") in ("AND", "OR"):
        return "(" + f" {item.get('key')} ".join(render(t, held) for t in terms(item)) + ")"
    body = ", ".join(f"{k}={v}" for k, v in params(item, held).items())
    return f"{item.get('key')}({body})"


def signals(root: ElementTree.Element) -> dict[str, tuple[str, list[ElementTree.Element]]]:
    """Every signal the strategy computes, by variable name, as its operator and its terms.

    Args:
        root: Parsed strategy_Portfolio.xml.

    Returns:
        {"LongEntrySignal": ("AND", [item, item]), "LongExitSignal": ("", [item])}. A signal
        whose top is not an AND/OR is one term with operator "", as logic.conditions reads
        it; an empty signal is left out.
    """
    names = {v.findtext("id"): v.findtext("name") for v in root.iter("variable")}
    out = {}
    for signal in root.iter("signal"):
        top = signal.find("Item")
        if top is None:
            continue
        op = top.get("key") if top.get("key") in ("AND", "OR") else ""
        out[names[signal.get("variable")]] = (op, terms(top) if op else [top])
    return out


def conditions(root: ElementTree.Element, exits: bool) -> list[dict]:
    """The entry or the exit conditions, one row each, with their parameters.

    Args:
        root: Parsed strategy_Portfolio.xml.
        exits: False for the `…EntrySignal` signals, True for the `…ExitSignal` ones.

    Returns:
        Rows with `signal`, `operator`, `index`, `block`, `params` and `text`. The first four
        are what sqx.structural.logic.conditions returns for a template-built strategy
        (tests/test_strategymeta.py holds them equal). Its regex misses the generic
        builder's AND, which carries attributes, and reads that signal as one condition
        keyed "AND"; the tree walk here reads its terms.
    """
    held, out = values(root), []
    for signal, (op, items) in signals(root).items():
        if not signal.endswith("ExitSignal" if exits else "EntrySignal"):
            continue
        out += [{"signal": signal, "operator": op, "index": i, "block": item.get("key"),
                 "params": params(item, held), "text": render(item, held)}
                for i, item in enumerate(items)]
    return out


def rule_lines(rows: list[dict]) -> dict[str, str]:
    """Each signal as one line, its terms joined by their operator."""
    out = {}
    for row in rows:
        out.setdefault(row["signal"], []).append(row["text"])
    ops = {r["signal"]: r["operator"] or "AND" for r in rows}
    return {s: f" {ops[s]} ".join(parts) for s, parts in out.items()}


def _formula(param: ElementTree.Element, held: dict[str, str]) -> dict | None:
    """An exit method's formula and its parameters, or None when it is SQX's `…None`."""
    formula = param.find("Formula")
    kind = formula.get("key").rsplit(".", 1)[1]
    if kind == "None":
        return None
    return {"formula": kind, **{p.get("key").strip("#"): _value(p, held)
                                for p in formula.findall("Param")}}


def orders(root: ElementTree.Element) -> list[dict]:
    """Every entry order, with its side and the exit methods it carries.

    Args:
        root: Parsed strategy_Portfolio.xml.

    Returns:
        One row per `Enter…` block: `type`, `direction`, and `stop_loss`, `profit_target`,
        `trailing_stop`, `break_even` (None, or the formula and its values — a stop grafted
        by sqx.variants.build.stoploss reads `ATRBasedValue` like one SQX built) and
        `exit_after_bars` (None when 0).
    """
    held, out = values(root), []
    for item in root.iter("Item"):
        if not (item.get("key") or "").startswith("Enter"):
            continue
        p = {c.get("key"): c for c in item if c.tag == "Param"}
        bars = _value(p["#ExitAfterBars.ExitAfterBars#"], held)
        out.append({"type": item.get("key"), "direction": SIDE[int(p["#Direction#"].text)],
                    **{name: _formula(p[key], held) for name, key in EXIT_METHODS.items()},
                    "exit_after_bars": int(bars) or None})
    return out


def direction(portfolio: str) -> str:
    """long, short or both, as sqx.structural.logic.direction reads the entry orders."""
    sides = set(logic.direction(portfolio))
    return "both" if len(sides) == 2 else SIDE[sides.pop()]
