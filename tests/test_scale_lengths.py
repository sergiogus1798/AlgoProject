#!/usr/bin/env python3
"""Cross TF scaling (owner, 2026-10-02: «arregla el escalado»): every bar-length parameter moves
with the timeframe — what SQX types `ParamTypePeriod`, the custom-block lengths `lengths.yaml`
rules, the exit after bars — and nothing else does: levels, multipliers, shifts, selectors."""

import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.variants import lengths, scale
from sqx.variants.build import rewrite

# (variable, type, value, SQX paramType)
VARIABLES = [
    ("StochSlowDCrossKPrd1", "int", "5", "ParamTypePeriod"),
    ("StochSlowDCrossDPrd1", "int", "3", "ParamTypePeriod"),
    ("StochSlowDCrossSlw1", "int", "3", "ParamTypePeriod"),
    ("StochSlowDCrsMAMth1", "int", "0", "ParamTypeOtherParam"),
    ("StochSlowDCrossLvl1", "double", "80", "ParamTypeConstant"),
    ("StochSlowDCrossShf1", "int", "1", "ParamTypeShift"),
    ("MACDMainFast1", "int", "12", "ParamTypePeriod"),
    ("MACDMainSlow1", "int", "26", "ParamTypePeriod"),
    ("MACDMainSmooth1", "int", "9", "ParamTypePeriod"),
    ("CBlock_ATRRankInt21", "int", "12", "ParamTypeOtherParam"),
    ("CBlock_ATRRankInt31", "int", "120", "ParamTypeOtherParam"),
    ("CBlock_ATRRankDbl31", "double", "50", "ParamTypeOtherParam"),
    ("CBlc_WAEPsAbvExpPrd51", "int", "90", "ParamTypePeriod"),
    ("CBlock_NobodyInt11", "int", "7", "ParamTypeOtherParam"),
    ("BarsPeriodShift1", "int", "1", "ParamTypeShift"),
    ("ExitAfterBars1", "int", "16", "ParamTypeExitUsed"),
]
# (block, parameter key, variable): how the rules bind each variable
BOUND = [
    ("StochSlowDCrossUp", "KPeriod", "StochSlowDCrossKPrd1"),
    ("StochSlowDCrossUp", "DPeriod", "StochSlowDCrossDPrd1"),
    ("StochSlowDCrossUp", "Slowing", "StochSlowDCrossSlw1"),
    ("StochSlowDCrossUp", "MAMethod", "StochSlowDCrsMAMth1"),
    ("StochSlowDCrossUp", "Level", "StochSlowDCrossLvl1"),
    ("StochSlowDCrossUp", "Shift", "StochSlowDCrossShf1"),
    ("MACDMainHigherSignal", "Fast", "MACDMainFast1"),
    ("MACDMainHigherSignal", "Slow", "MACDMainSlow1"),
    ("MACDMainHigherSignal", "Smooth", "MACDMainSmooth1"),
    ("CBlock_ATRRankHighVol", "Int2", "CBlock_ATRRankInt21"),
    ("CBlock_ATRRankHighVol", "Int3", "CBlock_ATRRankInt31"),
    ("CBlock_ATRRankHighVol", "Double3", "CBlock_ATRRankDbl31"),
    ("CBlock_WAEPosAboveExplosion", "Period5", "CBlc_WAEPsAbvExpPrd51"),
    ("CBlock_NobodyListedThis", "Int1", "CBlock_NobodyInt11"),
    ("MAFalling", "Shift", "BarsPeriodShift1"),
    ("EnterAtMarket", "ExitAfterBars.ExitAfterBars", "ExitAfterBars1"),
]


def portfolio() -> str:
    """A strategy_Portfolio.xml as SQX writes one, reduced to what the scaling reads."""
    declared = "".join(f"<variable><id>{n}</id><name>{n}</name><type>{t}</type><value>{v}</value>"
                       f"<paramType>{k}</paramType></variable>" for n, t, v, k in VARIABLES)
    rules, last = "", ""
    for block, key, name in BOUND:
        if block != last:
            rules += ("</Item>" if last else "") + f'<Item customSnippet="false" key="{block}">'
            last = block
        rules += (f'<Param key="#{key}#" controlType="jspinnerVar" type="int" variable="true">'
                  f"{name}</Param>")
    return (f'<?xml version="1.0" encoding="UTF-8"?><StrategyFile><Variables>{declared}'
            f"</Variables><Rules>{rules}</Item></Rules></StrategyFile>")


def sibling(target: str) -> dict:
    """The manifest row `scale.sibling` writes for the golden strategy, H1 to `target`."""
    with tempfile.TemporaryDirectory() as tmp:
        mother = Path(tmp) / "Mother.sqx"
        with zipfile.ZipFile(mother, "w") as z:
            z.writestr("META-INF/MANIFEST.MF", "")
            z.writestr(rewrite.SETTINGS, '<ResultsGroup ResultName="Mother"><StrategyName '
                                         'type="String">Mother</StrategyName></ResultsGroup>')
            z.writestr(rewrite.PORTFOLIO, portfolio())
        row = scale.sibling(mother, Path(tmp), "H1", target, scale.knobs(), 0)
        written = rewrite.values(rewrite.members(Path(row["path"]))[rewrite.PORTFOLIO].decode())
    return row | {"written": written}


def test_every_length_moves_and_nothing_else() -> None:
    """Stochastic (5,3,3) is (10,6,6) on the twice-faster timeframe; MACD (12,26,9) is
    (24,52,18); the custom block's two lengths double and its level stays; the exit doubles."""
    got = sibling("M30")
    w = got["written"]
    assert [w[n] for n in ("StochSlowDCrossKPrd1", "StochSlowDCrossDPrd1",
                           "StochSlowDCrossSlw1")] == ["10", "6", "6"]
    assert [w[n] for n in ("MACDMainFast1", "MACDMainSlow1", "MACDMainSmooth1")] == \
        ["24", "52", "18"]
    assert (w["CBlock_ATRRankInt21"], w["CBlock_ATRRankInt31"], w["CBlock_ATRRankDbl31"]) == \
        ("24", "240", "50")
    assert w["ExitAfterBars1"] == "32" and got["max_rounding_shift"] == 0 and not got["clamped"]
    assert (w["StochSlowDCrossLvl1"], w["StochSlowDCrossShf1"], w["StochSlowDCrsMAMth1"]) == \
        ("80", "1", "0")
    # typed a period by SQX and named like one, and still a multiplier: the table rules it
    assert w["CBlc_WAEPsAbvExpPrd51"] == "90"
    # named like a period, typed a shift: the name is only a fallback
    assert w["BarsPeriodShift1"] == "1"
    assert got["n_scaled"] == 9


def test_slower_rounds_clamps_and_flags_what_nobody_ruled() -> None:
    """On H4 MACD is (3,7,2) with 26/4 = 6.5 rounded up; the Stochastic's 3 and 3 fall under
    the floor and clamp; a custom block the table does not list is left alone and flagged."""
    got = sibling("H4")
    w = got["written"]
    assert [w[n] for n in ("MACDMainFast1", "MACDMainSlow1", "MACDMainSmooth1")] == \
        ["3", "7", "2"]
    assert (w["StochSlowDCrossDPrd1"], w["StochSlowDCrossSlw1"]) == ("2", "2") and got["clamped"]
    assert (w["CBlock_ATRRankInt21"], w["CBlock_ATRRankInt31"], w["ExitAfterBars1"]) == \
        ("3", "30", "4")
    # WAE's Sensetive joins it since encargo 47: `ranges.yaml` rules it a coefficient on a
    # one-bar change, which moves with the bar and not by the ATR ratio
    assert w["CBlock_NobodyInt11"] == "7"
    assert got["unverified"] == "CBlock_NobodyInt11,CBlc_WAEPsAbvExpPrd51"


def test_the_table_lists_every_custom_block_of_the_v3_palettes() -> None:
    """A ruling is one of three words, and no v3 palette draws a custom block without a row."""
    import yaml
    table = lengths.table()
    said = {r for row in table.values() for r in (row.values() if isinstance(row, dict) else [row])}
    assert said <= {"length", "other", "unverified"}
    palettes = Path(__file__).resolve().parent.parent / "sqx" / "blocks" / "palettes"
    drawn = {k for f in palettes.glob("*_v3.yaml")
             for k, w in (yaml.safe_load(f.read_text(encoding="utf-8")).get("overrides") or {}).items()
             if w and k.startswith(lengths.CUSTOM)}
    assert drawn and drawn <= set(table)


# Two blocks as SQX writes them in a BUILT strategy: the signal on the main chart and the
# moving-average filter on the D1 subchart, each with its own #Chart# and its own period.
TWO_CHARTS = """<StrategyFile><Strategy><Rules>
  <Item key="AroonCrossesAbove">
    <Param key="#Chart#" controlType="dataVar" type="data">0</Param>
    <Param key="#Period#" controlType="jspinnerVar" type="int" variable="true">AroonPeriod1</Param>
  </Item>
  <Item key="MovingAverage">
    <Param key="#Chart#" controlType="dataVar" type="data">1</Param>
    <Param generated="random" randomId="MovingAverage1" key="#Period#" type="int" variable="true">MovingAverage1</Param>
  </Item>
</Rules><Variables>
  <variable><name>AroonPeriod1</name><type>int</type><value>14</value>
    <paramType>ParamTypePeriod</paramType></variable>
  <variable><name>MovingAverage1</name><type>int</type><value>50</value>
    <paramType>ParamTypePeriod</paramType></variable>
</Variables></Strategy></StrategyFile>"""


def test_a_filter_on_another_chart_is_not_rescaled() -> None:
    """The D1 filter's period is already in its own bars: scaling it would move the filter.

    The filter's parameter is spelt as the builder writes a period it drew, `generated=`
    before `key=`: the first real build (2026-10-09) bound it that way and was missed."""
    assert lengths.off_main(TWO_CHARTS) == {"MovingAverage1"}
    scaled, unverified = lengths.split(TWO_CHARTS, [], lengths.table())
    assert scaled == ["AroonPeriod1"], scaled
    assert "MovingAverage1" not in scaled + unverified


if __name__ == "__main__":
    test_every_length_moves_and_nothing_else()
    test_slower_rounds_clamps_and_flags_what_nobody_ruled()
    test_the_table_lists_every_custom_block_of_the_v3_palettes()
    test_a_filter_on_another_chart_is_not_rescaled()
    print("ok")
