"""Add an ATR stop loss to a strategy that has none, as a declared parameter the factory can move."""

import re

VARIABLE = "StopLossCoef1"
PERIOD = 20

# The #StopLoss.StopLoss# parameter of an entry, holding the "no stop" formula. Only that one:
# #ProfitTarget.ProfitTarget# carries the very same SLPT.None and must stay untouched.
EMPTY = re.compile(r'(<Param key="#StopLoss\.StopLoss#"[^>]*>\s*)<Formula key="SQ\.Formulas\.SLPT\.None" />')
ENTRY = re.compile(r'<Item\b[^>]*key="Enter(?:AtMarket|AtStop|AtLimit)"')
# What SQX itself writes for `SL = X * ATR(20)`, copied from tests/fixtures/strategy.sqx.
FORMULA = ('<Formula key="SQ.Formulas.SLPT.ATRBasedValue">\n'
           '{pad}  <Param key="#Value#" controlType="jspinnerVar" type="double" variable="true">'
           f'{VARIABLE}</Param>\n'
           '{pad}  <Param key="#AtrPeriod#" controlType="jspinnerVar" type="int">'
           f'{PERIOD}</Param>\n'
           '{pad}</Formula>')
DECLARATION = ('<variable makeExternal="true">\n'
               '{pad}  <id>{name}</id>\n'
               '{pad}  <name>{name}</name>\n'
               '{pad}  <type>double</type>\n'
               '{pad}  <value>{value}</value>\n'
               '{pad}  <paramType>ParamTypeExitUsed</paramType>\n'
               '{pad}  <makeExternal>true</makeExternal>\n'
               '{pad}</variable>\n{pad}')
FIRST_VARIABLE = re.compile(r"([ \t]*)<variable\b")


def graft(portfolio: str, x: float) -> str:
    """The same strategy with `SL = x * ATR(20)` on every entry, and x declared as a parameter.

    Text substitution, never an XML round trip: the rest of the file stays byte-identical.
    Every entry order gets the stop, and the count is asserted — an entry left without it
    would still trade unprotected and nothing downstream would say so.

    Args:
        portfolio: Text of `strategy_Portfolio.xml` of a strategy built without a stop.
        x: The multiple of ATR(20), written as the variable's value.

    Returns:
        The rewritten text. Raises ValueError when the strategy already declares the
        variable or when the stops replaced are not one per entry order.
    """
    if f"<id>{VARIABLE}</id>" in portfolio:
        raise ValueError(f"the strategy already declares {VARIABLE}")

    def one(match: re.Match) -> str:
        """One entry's empty stop, replaced by the ATR formula at the same indentation."""
        pad = match.group(1).rsplit("\n", 1)[-1]
        return match.group(1) + FORMULA.format(pad=pad)

    out, n = EMPTY.subn(one, portfolio)
    entries = len(ENTRY.findall(portfolio))
    if n != entries or n == 0:
        raise ValueError(f"{n} stops replaced for {entries} entry orders")
    first = FIRST_VARIABLE.search(out)
    pad = first.group(1)
    value = f"{x:g}"
    return (out[:first.start()] + pad + DECLARATION.format(pad=pad, name=VARIABLE, value=value)
            + out[first.start() + len(pad):])
