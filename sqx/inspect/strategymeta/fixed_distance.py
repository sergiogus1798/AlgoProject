"""Fixed-distance (pips) parameters in a strategy's XML: stop, target, trailing, break-even, filters."""

import zipfile
from pathlib import Path
from xml.etree import ElementTree

from sqx.inspect.strategymeta.rules import _value, values

# Exit-method parameters (key as in <Item key="Enter…">), by name.
EXIT_PARAMS = {"#StopLoss.StopLoss#": "stop_loss", "#ProfitTarget.ProfitTarget#": "profit_target",
               "#TrailingStop.TrailingStop#": "trailing_stop",
               "#TrailingStop.TrailingActivation#": "trailing_activation",
               "#MoveSL2BE.MoveSL2BE#": "break_even", "#MoveSL2BE.SL2BEAddPips#": "break_even_add"}
# Formulas SQX's config labels «Fixed value (in pips)» / «Range in pips». ATRBasedValue,
# PctValue, PriceLevel, ValueFromFormula and None are not fixed distances.
FIXED_FORMULAS = {"SLPT.FixedValue", "RangeLevel.FixedValue", "Range.FixedValue",
                  "RangeLevel.PriceRange", "Range.PriceRange"}
# Condition blocks that carry a pips quantity: FixedPips holds it in #Value#; the P/L-in-pips
# readers are a distance only against the Number they are compared with.
PIPS_VALUE_BLOCK = "FixedPips"
PIPS_READERS = {"OpenPLInPips", "ClosedPLInPips", "SpreadInPips"}


def _root(source: "str | Path | ElementTree.Element") -> ElementTree.Element:
    """The parsed strategy_Portfolio.xml of a path, XML text or an already parsed root."""
    if isinstance(source, ElementTree.Element):
        return source
    text = str(source)
    if text.lstrip().startswith("<"):
        return ElementTree.fromstring(text)
    with zipfile.ZipFile(text) as z:
        return ElementTree.fromstring(z.read("strategy_Portfolio.xml"))


def _number(item: ElementTree.Element | None, held: dict[str, str]) -> float | None:
    """The value of a `Number` block, or None."""
    if item is None or item.get("key") != "Number":
        return None
    return float(_value(item.find("Param"), held))


def fixed_distances(source: "str | Path | ElementTree.Element") -> list[dict]:
    """Every fixed pips/points distance a strategy carries; empty when it has none.

    Args:
        source: A `.sqx` path, the text of strategy_Portfolio.xml, or its parsed root.

    Returns:
        Rows `{rule, where, param, formula, value, unit}`. `rule` is the rule it sits in ("Long
        entry"), `where` is "order" (exit method of an Enter block) or "condition", `param`
        names the stop_loss, profit_target, trailing_stop, trailing_activation, break_even,
        break_even_add, or the block of a condition. `value` is the number with a variable
        reference resolved. `unit` is "pips": SQX has no separate points unit.
    """
    root, out = _root(source), []
    held = values(root)
    parent = {c: p for p in root.iter() for c in p}
    rule_of = {}
    for rule in root.iter("Rule"):
        for node in rule.iter():
            rule_of[node] = rule.get("name") or ""

    for item in root.iter("Item"):
        key, rule = item.get("key") or "", rule_of.get(item, "")
        if key.startswith("Enter"):
            for p in item.findall("Param"):
                name, formula = EXIT_PARAMS.get(p.get("key")), p.find("Formula")
                if name is None or formula is None:
                    continue
                kind = formula.get("key").replace("SQ.Formulas.", "")
                if kind in FIXED_FORMULAS:
                    value = float(_value(formula.find("Param"), held))
                    out.append({"rule": rule, "where": "order", "param": name, "formula": kind,
                                "value": value, "unit": "pips"})
        elif key == PIPS_VALUE_BLOCK:
            out.append({"rule": rule, "where": "condition", "param": key, "formula": key,
                        "value": float(_value(item.find("Param"), held)), "unit": "pips"})
        elif key in PIPS_READERS:
            sides = [c.find("Item") for c in parent[parent[item]] if c.tag == "Block"]
            other = [n for s in sides if s is not item and (n := _number(s, held)) is not None]
            if other:
                out.append({"rule": rule, "where": "condition", "param": key, "formula": key,
                            "value": other[0], "unit": "pips"})
    return out
