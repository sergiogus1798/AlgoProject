"""Which coefficients of a strategy multiply a per-bar measure, and the ATR ratio they move by."""

import re
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import yaml

from core import assetdata, barstore
from sqx.variants import lengths
from sqx.variants.build import rewrite
from typing import Any, cast

TABLE = Path(__file__).with_name("ranges.yaml")
BAR, WINDOW, OTHER, UNVERIFIED = "bar", "window", "other", "unverified"
BUILTIN = "_builtin"
CONSTANT = "ParamTypeConstant"
# What SQX writes for a distance: `SLPT` for stop and target, other namespaces for the rest.
FORMULA = re.compile(
    r'(<Formula key="SQ\.Formulas\.\w+\.(\w+)">)(.*?)(</Formula>)', re.S
)
VALUE = re.compile(r'(<Param\b[^>]*\bkey="#Value#"[^>]*>)([^<]+)(</Param>)')
ATR_PERIOD = re.compile(r'(<Param\b[^>]*\bkey="#AtrPeriod#"[^>]*>)([^<]+)(</Param>)')
ATR_BASED = "ATRBasedValue"
# A distance that is not a multiple of anything: pips or a percent of price (proposal 4.3, row 3).
FIXED = ("FixedValue", "PctValue")
# What the manifest calls an ATR coefficient written as a literal, which no variable names.
LITERAL = "ATRBasedValue.Value"


def table() -> dict[str, Any]:
    """The reviewed rulings of ranges.yaml: block to parameter key to its measure."""
    return yaml.safe_load(TABLE.read_text(encoding="utf-8"))


def _bound(portfolio: str) -> dict[str, str]:
    """Variables a distance formula's `#Value#` is bound to, each with the formula's kind."""
    found = {}
    for _, kind, body, _ in FORMULA.findall(portfolio):
        value = VALUE.search(body)
        if value and 'variable="true"' in value.group(1):
            found[value.group(2).strip()] = kind
    return found


def measures(portfolio: str, rulings: dict) -> dict[str, str]:
    """What every non-length parameter of a strategy was ruled to multiply.

    A variable bound to a distance formula is ruled by the formula's kind; a custom block's
    parameter by its row, and its unlisted double is unverified; a built-in block's double by
    the first `_builtin` rule that matches, else by SQX's own type — a `ParamTypeConstant`
    is a level, anything else an unruled coefficient.

    Args:
        portfolio: Text of `strategy_Portfolio.xml`.
        rulings: Output of `table`.

    Returns:
        Variable to `bar`, `window`, `other` or `unverified`, in declaration order. A
        variable this table has nothing to say about (an int that `lengths` rules, a level,
        a file older than `<paramType>`) is absent.
    """
    types, kind = rewrite.declared(portfolio), lengths.kinds(portfolio)
    owner, bound = lengths.owners(portfolio), _bound(portfolio)
    found = {}
    for name, typed in types.items():
        block, param = owner.get(name, ("", ""))
        if name[0].isdigit() or typed == "boolean":
            continue
        if name in bound:
            found[name] = (
                BAR
                if bound[name] == ATR_BASED
                else OTHER
                if bound[name] in FIXED
                else UNVERIFIED
            )
        elif block.startswith(lengths.CUSTOM):
            listed = rulings.get(block) or {}
            if param in listed or typed == "double":
                found[name] = listed.get(param, UNVERIFIED)
        elif typed == "double":
            rule = next(
                (
                    r["measure"]
                    for r in rulings[BUILTIN]
                    if re.search(r["block"], block) and re.fullmatch(r["param"], param)
                ),
                None,
            )
            if rule or kind[name] not in ("", CONSTANT):
                found[name] = rule or UNVERIFIED
    return found


def stops(
    portfolio: str, c: float | None, period: Callable[[float], dict]
) -> tuple[str, int, list[dict]]:
    """The same strategy with every literal of its ATR distances moved to the sibling's bars.

    A coefficient bound to a variable is `measures`' business; this is for what the formula
    carries as a number — always the ATR period of a grafted stop, sometimes the coefficient.

    Args:
        portfolio: Text of `strategy_Portfolio.xml`.
        c: Output of `ratio`, or None when it could not be measured: coefficients stay.
        period: One literal period to its `scale.rescaled` entry (`written`, `shift`, ...).

    Returns:
        (text, literal coefficients found, the entries of the literal periods rewritten). The
        coefficients were divided by `c` only when `c` is given.
    """
    coefs, periods = 0, []

    def one(match: re.Match) -> str:
        """One distance formula: untouched unless it is ATR-based."""
        nonlocal coefs
        opening, kind, body, closing = match.groups()
        if kind != ATR_BASED:
            return match.group(0)

        def value(m: re.Match) -> str:
            """A literal coefficient divided by c; one bound to a variable left as it is."""
            nonlocal coefs
            if 'variable="true"' in m.group(1):
                return m.group(0)
            coefs += 1
            return (
                m.group(1)
                + (f"{float(m.group(2)) / c:.6g}" if c else m.group(2))
                + m.group(3)
            )

        def bars(m: re.Match) -> str:
            """A literal ATR period rescaled like any other length."""
            if 'variable="true"' in m.group(1):
                return m.group(0)
            periods.append(period(float(m.group(2))))
            return m.group(1) + str(int(periods[-1]["written"])) + m.group(3)

        return opening + ATR_PERIOD.sub(bars, VALUE.sub(value, body)) + closing

    return FORMULA.sub(one, portfolio), coefs, periods


def atr(bars: pd.DataFrame, period: int) -> pd.Series:
    """Wilder's average true range, one value per bar, in price.

    Args:
        bars: Bars with High, Low and Close, in time order.
        period: The ATR period, in bars.

    Returns:
        The true range smoothed at 1/period. Its start differs from SQX's averaged one for
        a few periods, which a median over years does not see.
    """
    prev = bars["Close"].shift()
    true_range = pd.concat(
        [
            bars["High"] - bars["Low"],
            (bars["High"] - prev).abs(),
            (bars["Low"] - prev).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return cast("pd.Series", true_range.ewm(alpha=1 / period, adjust=False).mean())


def ratio(
    mother: pd.DataFrame, sibling: pd.DataFrame, period: int, scaled: int
) -> float:
    """c: how much bigger the sibling's typical bar is than the mother's (proposal 4.2).

    Args:
        mother: The market's bars on the mother's timeframe.
        sibling: The same market and span on the sibling's timeframe.
        period: The ATR period on the mother's timeframe.
        scaled: That period as the sibling carries it, already rescaled.

    Returns:
        Median ATR of the sibling's bars over median ATR of the mother's. About the square
        root of the timeframe ratio for a random walk; measured because intraday it is not.
    """
    return float(atr(sibling, scaled).median() / atr(mother, period).median())


def measured(symbol: str, source: str, target: str, period: int, scaled: int) -> float:
    """`ratio` for one asset and timeframe pair, over build + oos1 of the bar library.

    Args:
        symbol: An asset of `assets/`, e.g. "NIKKEI225".
        source, target: The mother's timeframe and the sibling's.
        period, scaled: As `ratio` takes them.

    Returns:
        c. A property of the market, not of a strategy: one number per batch and target.
    """
    data = assetdata.load(symbol)
    start = pd.Timestamp(assetdata.window(data, "build")[0], unit="ms")
    end = pd.Timestamp(assetdata.window(data, "oos1")[1], unit="ms")

    def bars(timeframe: str) -> pd.DataFrame:
        """The asset's bars on one timeframe, build through oos1."""
        frame = barstore.read(data["sqx_symbol"], timeframe)
        return cast("pd.DataFrame", frame[(frame.index >= start) & (frame.index < end)])

    return ratio(bars(source), bars(target), period, scaled)
