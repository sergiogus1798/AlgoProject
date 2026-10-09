"""Which variables of a strategy are lengths in bars: SQX's type, the custom-block table, the name."""

import re
from pathlib import Path

import yaml

from sqx.variants.build import rewrite

TABLE = Path(__file__).with_name("lengths.yaml")
PERIOD, SHIFT = "ParamTypePeriod", "ParamTypeShift"
KIND = re.compile(r"<paramType>([^<]*)</paramType>")
# A rule item opening, or a parameter of the item above it bound to a variable.
BOUND = re.compile(r'<Item\b[^>]*\bkey="([^"]+)"|<Param key="#([^"#]+)#"[^>]*variable="true"[^>]*>'
                   r"([^<]+)</Param>")
CUSTOM = "CBlock_"


def table() -> dict:
    """The reviewed rulings of lengths.yaml: custom block to parameter key to its ruling."""
    return yaml.safe_load(TABLE.read_text(encoding="utf-8"))


def kinds(portfolio: str) -> dict[str, str]:
    """Every variable's `<paramType>` as SQX wrote it; empty for a file older than the field."""
    return {rewrite.FIELD["name"].search(b).group(1): (KIND.search(b) or [None, ""])[1]
            for b in rewrite.VARIABLE.findall(portfolio)}


def owners(portfolio: str) -> dict[str, tuple[str, str]]:
    """Which block and which of its parameters each variable is bound to.

    Args:
        portfolio: Text of `strategy_Portfolio.xml`.

    Returns:
        Variable to (block key, parameter key without its hashes), read off the rules in
        document order: a `<Param variable="true">` belongs to the last `<Item>` opened.
    """
    found, block = {}, ""
    for item, param, name in BOUND.findall(portfolio):
        if item:
            block = item
        else:
            found[name] = (block, param)
    return found


def split(portfolio: str, patterns: list[str], rulings: dict) -> tuple[list[str], list[str]]:
    """The variables to rescale, and the ones nobody could rule on.

    A custom block's parameter is ruled by the table and by nothing else — SQX types a custom
    block's own parameters as it was told to, and WAE's `Sensetive` is typed a period while
    being a multiplier. Any other variable is a length when SQX typed it `ParamTypePeriod`;
    the name patterns are the fallback for what SQX types otherwise (`ExitAfterBars` is
    `ParamTypeExitUsed`) and for files written before the field existed. A shift never is.

    Args:
        portfolio: Text of `strategy_Portfolio.xml`.
        patterns: `crosstf.scale` of config.yaml, matched with `search` on the variable name.
        rulings: Output of `table`.

    Returns:
        (lengths, unverified), each in declaration order. An unverified variable is an int of
        a custom block the table rules `unverified` or does not list: it is left alone and
        its sibling must be read as not tested.
    """
    types, kind, owner = rewrite.declared(portfolio), kinds(portfolio), owners(portfolio)
    lengths, unverified = [], []
    for name, typed in types.items():
        block, param = owner.get(name, ("", ""))
        if name[0].isdigit() or typed == "boolean":
            continue
        if block.startswith(CUSTOM):
            listed = rulings.get(block)
            ruling = listed.get(param, "unverified") if isinstance(listed, dict) else "unverified"
            if ruling == "length":
                lengths.append(name)
            elif ruling == "unverified" and typed == "int":
                unverified.append(name)
        elif kind[name] == PERIOD or (kind[name] != SHIFT
                                      and any(re.search(p, name) for p in patterns)):
            lengths.append(name)
    return lengths, unverified
