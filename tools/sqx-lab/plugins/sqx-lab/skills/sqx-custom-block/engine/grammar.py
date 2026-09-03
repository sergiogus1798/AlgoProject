"""Portable SQX custom-block grammar — the build-STABLE core.

Operators, logical joiners, arithmetic value-functions, higher-order operators,
outer optimizer-knob Params, and the CBlock_* wrapper. None of these depend on a
particular install's indicator catalog, so they ship verbatim and are proven by
hundreds of import-confirmed blocks.

The install-SPECIFIC part (indicator atom schemas) is NOT here — it is discovered
from the user's own config.xml by bootstrap.py and emitted by emit.py.

Everything returns an XML string. Compose: an operator wraps value atoms; make_block
wraps the operator tree into a CBlock_* with its outer Params after </Contents>.

    from engine.grammar import is_greater, make_block, int_param, esc
    from engine.emit import Catalog
    cat = Catalog("catalog.json")
    block = make_block(
        key="CBlock_RSIAbove50",
        name="RSIAbove50",
        display=esc("RSI(@Chart@14) > 50"),
        category="MeanReversion_user",
        help_text="RSI above its midline.",
        opposite="CBlock_RSIBelow50",
        params=int_param("#Int2#", "Period", "14", "2", "100"),
        contents=is_greater(cat.atom("RSI", period="#Int2#"), cat.number("50")),
    )
"""

from __future__ import annotations

import re

# An outer optimizer-knob reference (#Int2#, #Double4#, ...). Operator params emit a
# customParam binding ONLY for these; a literal value stays plain text. Before this
# rule, is_rising/is_falling could never bind a knob (the literal "#Int2#" text landed
# in an int param, unresolvable at import), while the percentile/count/MA operators
# forced customParam even onto literals — both halves of audit finding B8.
_KNOB_REF_RE = re.compile(r"^#[A-Za-z]+\d+#$")


def _bindable(val) -> str:
    """` customParam="true" value="#IntN#"` when val is a knob reference, else ""."""
    return f' customParam="true" value="{val}"' if _KNOB_REF_RE.match(str(val)) else ""


# ---------------------------------------------------------------------------
# XML escaping — help/display text MUST escape these or AlgoWizard's parser
# breaks (lesson hit 3x: batch_002, batch_007, v144_009). Always wrap any
# human-authored display=/help= string in esc(). Since all grammar attributes
# are emitted inside double quotes, a raw " in the text used to break the WHOLE
# batch (audit P0-10) — esc() now escapes both quote kinds too, and the wrappers
# below escape name=/category= themselves (display/help stay caller-escaped).
# ---------------------------------------------------------------------------

def esc(text: str) -> str:
    """Escape &, <, >, \" and ' for safe use in an XML attribute (display=, help=)."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


# ---------------------------------------------------------------------------
# Outer Params (live AFTER </Contents> on the CBlock_* Item) — optimizer knobs
# ---------------------------------------------------------------------------

def chart_param() -> str:
    """Outer chart slot — every block needs exactly one."""
    return (
        '<Param name="Chart" display="Chart" key="#Chart1#" type="data"'
        ' paramType="data" controlType="dataVar" defaultValue="0"/>'
    )


def int_param(key: str, name: str, default: str, mn: str, mx: str, step: str = "1") -> str:
    """Outer integer optimizer knob. Keys: #Int2#, #Int3#, ... (144 convention).
    `name` is human text and is escaped here — pass it raw."""
    return (
        f'<Param name="{esc(name)}" type="int" paramType="int" key="{key}"'
        f' defaultValue="{default}" minValue="{mn}" maxValue="{mx}" step="{step}"'
        f' controlType="jspinnerVar">{default}</Param>'
    )


def double_param(key: str, name: str, default: str, mn: str, mx: str, step: str) -> str:
    """Outer double optimizer knob. Keys: #Double3#, #Double4#, ...
    `name` is human text and is escaped here — pass it raw."""
    return (
        f'<Param name="{esc(name)}" type="double" paramType="double" key="{key}"'
        f' defaultValue="{default}" minValue="{mn}" maxValue="{mx}" step="{step}"'
        f' controlType="jspinnerVar">{default}</Param>'
    )


# ---------------------------------------------------------------------------
# Comparison operators (boolean root of a condition block)
# ---------------------------------------------------------------------------

def _value_block(slot_key: str, slot_name: str, inner: str) -> str:
    return (
        f'<Block key="{slot_key}" name="{slot_name}" type="value"'
        f' controlType="value">{inner}</Block>'
    )


def is_greater(left: str, right: str) -> str:
    return (
        '<Item customSnippet="false" key="IsGreater" name="(&gt;) Is greater"'
        ' display="#Left# &gt; #Right#" returnType="boolean" mI="Comparisons"'
        ' categoryType="operators">'
        f'{_value_block("#Left#", "Left", left)}{_value_block("#Right#", "Right", right)}'
        '</Item>'
    )


def is_lower(left: str, right: str) -> str:
    return (
        '<Item customSnippet="false" key="IsLower" name="(&lt;) Is lower"'
        ' display="#Left# &lt; #Right#" returnType="boolean" mI="Comparisons"'
        ' categoryType="operators">'
        f'{_value_block("#Left#", "Left", left)}{_value_block("#Right#", "Right", right)}'
        '</Item>'
    )


def crosses_above(left: str, right: str) -> str:
    return (
        '<Item customSnippet="false" key="CrossesAbove" name="Crosses Above"'
        ' display="#Left# crosses above #Right#" returnType="boolean"'
        ' mI="Comparisons" categoryType="operators">'
        f'{_value_block("#Left#", "Left", left)}{_value_block("#Right#", "Right", right)}'
        '</Item>'
    )


def crosses_below(left: str, right: str) -> str:
    return (
        '<Item customSnippet="false" key="CrossesBelow" name="Crosses Below"'
        ' display="#Left# crosses below #Right#" returnType="boolean"'
        ' mI="Comparisons" categoryType="operators">'
        f'{_value_block("#Left#", "Left", left)}{_value_block("#Right#", "Right", right)}'
        '</Item>'
    )


def is_rising(value: str, bars: str = "2", shift: str = "1") -> str:
    """`value is rising` over #Bars# bars. Wraps a single value series.
    `bars` may be a literal ("3") or an outer knob reference ("#Int2#" — declare it)."""
    return (
        '<Item customSnippet="false" key="IsRising" name="Is rising"'
        ' display="#Indicator# is rising" returnType="boolean" mI="Comparisons"'
        ' categoryType="operators">'
        f'<Param key="#Bars#" name="Bars rising" type="int" defaultValue="2"'
        f' controlType="jspinnerVar" minValue="2" maxValue="100" step="1"'
        f' builderMaxValue="50" builderStep="1"{_bindable(bars)}>{bars}</Param>'
        '<Param key="#NotStrict#" name="Allow same values" type="boolean"'
        ' defaultValue="false" controlType="booleanVar" builderStep="1">false</Param>'
        f'<Param key="#Shift#" name="Shift" type="int" defaultValue="1"'
        f' controlType="jspinnerVar" minValue="0" maxValue="1000"'
        f' genMinValue="-1000001" genMaxValue="-1000002" paramType="shift"'
        f' step="1" builderMinValue="1" builderMaxValue="1" builderStep="1">{shift}</Param>'
        f'{_value_block("#Indicator#", "Indicator", value)}'
        '</Item>'
    )


def is_falling(value: str, bars: str = "2", shift: str = "1") -> str:
    """`value is falling` over #Bars# bars. `bars` literal or knob ref, like is_rising."""
    return (
        '<Item customSnippet="false" key="IsFalling" name="Is falling"'
        ' display="#Indicator# is falling" returnType="boolean" mI="Comparisons"'
        ' categoryType="operators">'
        f'<Param key="#Bars#" name="Bars falling" type="int" defaultValue="2"'
        f' controlType="jspinnerVar" minValue="2" maxValue="100" step="1"'
        f' builderMaxValue="50" builderStep="1"{_bindable(bars)}>{bars}</Param>'
        '<Param key="#NotStrict#" name="Allow same values" type="boolean"'
        ' defaultValue="false" controlType="booleanVar" builderStep="1">false</Param>'
        f'<Param key="#Shift#" name="Shift" type="int" defaultValue="1"'
        f' controlType="jspinnerVar" minValue="0" maxValue="1000"'
        f' genMinValue="-1000001" genMaxValue="-1000002" paramType="shift"'
        f' step="1" builderMinValue="1" builderMaxValue="1" builderStep="1">{shift}</Param>'
        f'{_value_block("#Indicator#", "Indicator", value)}'
        '</Item>'
    )


# ---------------------------------------------------------------------------
# Logical joiners — 144's shipped minimal form
# ---------------------------------------------------------------------------

def and_op(*clauses: str) -> str:
    return f'<Item key="AND">{"".join(f"<Block>{c}</Block>" for c in clauses)}</Item>'


def or_op(*clauses: str) -> str:
    return f'<Item key="OR">{"".join(f"<Block>{c}</Block>" for c in clauses)}</Item>'


# ---------------------------------------------------------------------------
# Arithmetic value-functions (return a VALUE; nest INSIDE a comparison).
# categoryType="other" mI="Functions"; ignoreInBuilder so the builder won't
# randomize the function node (knobs come from atoms nested inside).
# ---------------------------------------------------------------------------

def _binop(key: str, friendly: str, sym: str, left: str, right: str) -> str:
    return (
        f'<Item customSnippet="false" key="{key}" name="{friendly}"'
        f' display="(#Left# {sym} #Right#)" returnType="pricenumber"'
        f' ignoreInBuilder="true" mI="Functions" categoryType="other" help="">'
        f'{_value_block("#Left#", "Left", left)}{_value_block("#Right#", "Right", right)}'
        '</Item>'
    )


def plus(left: str, right: str) -> str:
    return _binop("Plus", "(+) Plus", "+", left, right)


def minus(left: str, right: str) -> str:
    return _binop("Minus", "(-) Minus", "-", left, right)


def mult(left: str, right: str) -> str:
    return _binop("Multiplication", "(*) Multiplication", "*", left, right)


def divide(left: str, right: str) -> str:
    return _binop("Division", "(/) Division", "/", left, right)


def abs_val(value: str) -> str:
    return (
        '<Item customSnippet="false" key="Abs" name="(ABS) Absolute value"'
        ' display="Abs(#Value#)" returnType="pricenumber" help="Absolute value of a number"'
        ' ignoreInBuilder="true" mI="Functions" categoryType="other">'
        f'{_value_block("#Value#", "Value", value)}</Item>'
    )


def maximum(value1: str, value2: str) -> str:
    return (
        '<Item customSnippet="false" key="Maximum" name="(MAX) Maximum"'
        ' display="Max(#Value1#, #Value2#)" returnType="pricenumber"'
        ' help="Maximum of two values" ignoreInBuilder="true" mI="Functions" categoryType="other">'
        f'{_value_block("#Value1#", "Value 1", value1)}{_value_block("#Value2#", "Value 2", value2)}</Item>'
    )


def minimum(value1: str, value2: str) -> str:
    return (
        '<Item customSnippet="false" key="Minimum" name="(MIN) Minimum"'
        ' display="Min(#Value1#, #Value2#)" returnType="pricenumber"'
        ' help="Minimum of two values" ignoreInBuilder="true" mI="Functions" categoryType="other">'
        f'{_value_block("#Value1#", "Value 1", value1)}{_value_block("#Value2#", "Value 2", value2)}</Item>'
    )


# ---------------------------------------------------------------------------
# Higher-order operators — wrap an indicator value, add their own knobs.
# Bind Bars/Period/Percentile to outer knobs via customParam value="#OuterKey#".
# ---------------------------------------------------------------------------

def _shift_param(shift: str) -> str:
    return (
        f'<Param key="#Shift#" name="Shift" type="int" defaultValue="1"'
        f' controlType="jspinnerVar" minValue="0" maxValue="1000"'
        f' genMinValue="-1000001" genMaxValue="-1000002" paramType="shift" step="1"'
        f' builderMinValue="1" builderMaxValue="1" builderStep="1">{shift}</Param>'
    )


def _percentil(key, friendly, phrase, indicator, bars_ref, pct_ref, shift):
    return (
        f'<Item customSnippet="true" key="{key}" name="{friendly}"'
        f' display="#Indicator# is {phrase} than #Percentile# % of the values over #Bars# bars in the past"'
        f' returnType="boolean" mI="Comparisons" categoryType="operators" help="">'
        f'<Param key="#Bars#" name="Bars" type="int" defaultValue="100" controlType="jspinnerVar"'
        f' minValue="2" maxValue="1000" step="1" builderMaxValue="1000" builderStep="1"'
        f'{_bindable(bars_ref)}>{bars_ref}</Param>'
        f'{_shift_param(shift)}'
        f'<Param key="#Percentile#" name="Percentile" type="double" defaultValue="80"'
        f' controlType="jspinnerVar" minValue="0.1" maxValue="99.9" step="0.1"'
        f' builderMaxValue="99.9" builderStep="0.1"{_bindable(pct_ref)}>{pct_ref}</Param>'
        f'{_value_block("#Indicator#", "Indicator", indicator)}</Item>'
    )


def percentile_above(indicator, bars_ref, pct_ref, shift="1"):
    """indicator >= P-th percentile of its own last #Bars# values (self-normalizing)."""
    return _percentil("IsGreaterPercentil", "(&gt; % Rank) Is Greater or Equal Percent Rank",
                      "greater or equal", indicator, bars_ref, pct_ref, shift)


def percentile_below(indicator, bars_ref, pct_ref, shift="1"):
    return _percentil("IsLowerPercentil", "(&lt; % Rank) Is Lower or Equal Percent Rank",
                      "lower or equal", indicator, bars_ref, pct_ref, shift)


_MA_TYPES = "Simple=1,Exponential=2,Weighted=3,Hull=4"


def _ind_vs_ma(key, friendly, phrase, indicator, period_ref, ma_type, shift):
    return (
        f'<Item customSnippet="false" key="{key}" name="{friendly}"'
        f' display="#Indicator# {phrase} its #MAType# MA(#Period#)"'
        f' returnType="boolean" mI="Comparisons" categoryType="operators">'
        f'<Param key="#Period#" name="Period" type="int" defaultValue="14" controlType="jspinnerVar"'
        f' minValue="2" maxValue="1000" step="1" builderStep="1"'
        f'{_bindable(period_ref)}>{period_ref}</Param>'
        f'<Param key="#MAType#" name="MA Type" type="int" controlType="combo"'
        f' values="{_MA_TYPES}" defaultValue="1">{ma_type}</Param>'
        f'{_shift_param(shift)}'
        f'{_value_block("#Indicator#", "Indicator", indicator)}</Item>'
    )


def ind_above_ma(indicator, period_ref, ma_type="2", shift="1"):
    """indicator above its own MA(period). ma_type 1=SMA 2=EMA 3=WMA 4=HMA."""
    return _ind_vs_ma("IndicatorAboveMA", "(I &gt; MA) Indicator Above MA", "is above",
                      indicator, period_ref, ma_type, shift)


def ind_below_ma(indicator, period_ref, ma_type="2", shift="1"):
    return _ind_vs_ma("IndicatorBelowMA", "(I &lt; MA) Indicator Below MA", "is below",
                      indicator, period_ref, ma_type, shift)


def ind_cross_above_ma(indicator, period_ref, ma_type="2", shift="1"):
    return _ind_vs_ma("IndicatorCrossesAboveMA", "(I MA) Indicator Crosses Above MA",
                      "crosses above", indicator, period_ref, ma_type, shift)


def ind_cross_below_ma(indicator, period_ref, ma_type="2", shift="1"):
    return _ind_vs_ma("IndicatorCrossesBelowMA", "(I MA) Indicator Crosses Below MA",
                      "crosses below", indicator, period_ref, ma_type, shift)


def _count(key, friendly, sym, left, right, bars_ref, shift):
    return (
        f'<Item customSnippet="false" key="{key}" name="{friendly}"'
        f' display="#IndicatorLeft# {sym} #IndicatorRight# is true #Bars# bars"'
        f' returnType="boolean" mI="Comparisons" categoryType="operators">'
        f'<Param key="#Bars#" name="Bars" type="int" defaultValue="3" controlType="jspinnerVar"'
        f' minValue="1" maxValue="1000" step="1" builderMaxValue="100" builderStep="1"'
        f'{_bindable(bars_ref)}>{bars_ref}</Param>'
        f'<Param key="#NotStrict#" name="Allow same values" type="boolean" defaultValue="false"'
        f' controlType="booleanVar" builderStep="1">false</Param>'
        f'{_shift_param(shift)}'
        f'{_value_block("#IndicatorLeft#", "Indicator Left", left)}'
        f'{_value_block("#IndicatorRight#", "Indicator Right", right)}</Item>'
    )


def count_greater(left, right, bars_ref, shift="1"):
    """left > right held true for the last #Bars# bars (persistence/noise filter)."""
    return _count("IsGreaterCount", "(&gt; X) Is greater for X bars", "&gt;",
                  left, right, bars_ref, shift)


def count_lower(left, right, bars_ref, shift="1"):
    return _count("IsLowerCount", "(&lt; X) Is lower for X bars", "&lt;",
                  left, right, bars_ref, shift)


# ---------------------------------------------------------------------------
# The CBlock_* wrapper
# ---------------------------------------------------------------------------

def make_block(key, name, display, category, help_text, opposite, params, contents):
    """One CBlock_* outer Item in 144 schema. `opposite` = partner key or "CBlock_null".

    Layout: <Item ... categoryType="Custom blocks"><Contents>{contents}</Contents>
            {chart_param()}{params}</Item>
    `display` and `help_text` must already be escaped (use esc()); `name` and
    `category` are escaped HERE — pass them raw (double-escaping would corrupt &amp;).
    """
    return (
        f'<Item category="{esc(category)}" oppositeBlockKey="{opposite}"'
        f' returnType="boolean" type="Condition" display="{display}" name="{esc(name)}"'
        f' key="{key}" help="{help_text}" categoryType="Custom blocks"'
        f' strategyType="Standard" status="0" action="add">'
        f'<Contents>{contents}</Contents>'
        f'{chart_param()}{params}'
        f'</Item>'
    )


def make_price_level(key, name, display, category, help_text, opposite, params, contents):
    """One CBlock_* outer Item as a PRICE-LEVEL block (returnType="price",
    type="Price level") — the value-returning sibling of make_block.

    A Price-level block RETURNS A PRICE (a stop/target/entry/breakout reference),
    not a true/false condition. `contents` is a single VALUE expression — one price
    atom (cat.atom("HighD")) or an arithmetic tree (plus/minus/mult/maximum/...
    over atoms + cat.number) — with NO and_op/comparison wrapper. `opposite` is the
    mirror-band partner key (upper<->lower) or "CBlock_null". display/help esc()'d
    by the CALLER; name/category are escaped here — pass them raw.
    """
    return (
        f'<Item category="{esc(category)}" oppositeBlockKey="{opposite}"'
        f' returnType="price" type="Price level" display="{display}" name="{esc(name)}"'
        f' key="{key}" help="{help_text}" categoryType="Custom blocks"'
        f' strategyType="Standard" status="0" action="add">'
        f'<Contents>{contents}</Contents>'
        f'{chart_param()}{params}'
        f'</Item>'
    )


def wrap_batch(blocks: list[str]) -> str:
    """Wrap emitted block strings into a <CustomBlocks> document."""
    return "<CustomBlocks>\n" + "\n".join(blocks) + "\n</CustomBlocks>\n"
