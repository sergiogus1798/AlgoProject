#!/usr/bin/env python3
"""Test for sqx.inspect.strategymeta.fixed_distance: fixed pips found, ATR/percent/level not."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.inspect.strategymeta.fixed_distance import fixed_distances

HERE = Path(__file__).parent / "fixtures"
SNAP = Path.home() / "Desktop/AlgoData/snapshots/weekly-data-update-2026-10-03/projects"


def _xml(sl: str = "", pt: str = "", trail: str = "", act: str = "", be: str = "", add: str = "", cond: str = "") -> str:
    """A minimal strategy: one Long entry order with the given exit-method formulas."""
    def p(key: str, ctl: str, formula: str) -> str:
        """One exit-method Param."""
        return f'<Param key="{key}" controlType="{ctl}" exitMethod="true">{formula}</Param>' if formula else ""
    atr = '<Formula key="SQ.Formulas.SLPT.ATRBasedValue"><Param key="#Value#">4.4</Param><Param key="#AtrPeriod#">20</Param></Formula>'
    return f"""<Strategy><variables><variable><id>Pips1</id><name>Pips1</name><value>77</value></variable></variables>
<Rule name="Long entry"><If>{cond}</If><Then><Item key="EnterAtMarket">
{p("#StopLoss.StopLoss#", "SLPT", sl or atr)}{p("#ProfitTarget.ProfitTarget#", "SLPT", pt)}
{p("#TrailingStop.TrailingStop#", "RangeLevel", trail)}{p("#TrailingStop.TrailingActivation#", "Range", act)}
{p("#MoveSL2BE.MoveSL2BE#", "RangeLevel", be)}{p("#MoveSL2BE.SL2BEAddPips#", "Range", add)}
</Item></Then></Rule></Strategy>"""


def _fixed(kind: str, value: str = "50", var: bool = False) -> str:
    """A fixed-value Formula."""
    v = f'<Param key="#Value#" variable="true">{value}</Param>' if var else f'<Param key="#Value#">{value}</Param>'
    return f'<Formula key="SQ.Formulas.{kind}">{v}</Formula>'


def test_atr_pct_level_none_are_not_fixed() -> None:
    """Atr pct level none are not fixed."""
    pct = '<Formula key="SQ.Formulas.SLPT.PctValue"><Param key="#Value#">1</Param></Formula>'
    lvl = '<Formula key="SQ.Formulas.SLPT.PriceLevel"><Param key="#Value#">x</Param></Formula>'
    none = '<Formula key="SQ.Formulas.RangeLevel.None" />'
    assert fixed_distances(_xml(pt=pct, trail=lvl, be=none)) == []


def test_each_exit_method_is_named() -> None:
    """Each exit method is named."""
    xml = _xml(sl=_fixed("SLPT.FixedValue", "30"), pt=_fixed("SLPT.FixedValue", "60"),
               trail=_fixed("RangeLevel.FixedValue", "93"), act=_fixed("Range.FixedValue", "60"),
               be=_fixed("RangeLevel.FixedValue", "217"), add=_fixed("Range.FixedValue", "10"))
    got = {r["param"]: r["value"] for r in fixed_distances(xml)}
    assert got == {"stop_loss": 30, "profit_target": 60, "trailing_stop": 93,
                   "trailing_activation": 60, "break_even": 217, "break_even_add": 10}
    assert {r["rule"] for r in fixed_distances(xml)} == {"Long entry"}


def test_variable_reference_is_resolved() -> None:
    """Variable reference is resolved."""
    (row,) = fixed_distances(_xml(sl=_fixed("SLPT.FixedValue", "Pips1", var=True)))
    assert row["value"] == 77 and row["unit"] == "pips"


def test_fixed_pips_block_in_a_condition() -> None:
    """Fixed pips block in a condition."""
    cond = '<Item key="IsGreater"><Block key="#Right#"><Item key="FixedPips"><Param key="#Value#">160</Param></Item></Block></Item>'
    (row,) = fixed_distances(_xml(cond=cond))
    assert (row["where"], row["param"], row["value"]) == ("condition", "FixedPips", 160)


def test_pl_in_pips_needs_a_number_to_compare_with() -> None:
    """Pl in pips needs a number to compare with."""
    def cmp(right: str) -> str:
        """A comparison of OpenPLInPips with `right`."""
        return ('<Item key="IsGreater"><Block key="#Left#"><Item key="OpenPLInPips"><Param key="#Symbol#">x</Param></Item></Block>'
                f'<Block key="#Right#">{right}</Block></Item>')
    num = '<Item key="Number"><Param key="#Number#">25</Param></Item>'
    assert [r["value"] for r in fixed_distances(_xml(cond=cmp(num)))] == [25]
    assert fixed_distances(_xml(cond=cmp('<Item key="Close"><Param key="#Shift#">1</Param></Item>'))) == []


def test_accepts_a_parsed_root() -> None:
    """Accepts a parsed root."""
    from xml.etree import ElementTree
    root = ElementTree.fromstring(_xml(trail=_fixed("RangeLevel.FixedValue")))
    assert len(fixed_distances(root)) == 1


# Real files, when the snapshot is on disk.
@pytest.mark.skipif(not SNAP.exists(), reason="snapshot not on this machine")
def test_real_strategies() -> None:
    """Real strategies."""
    gbp = SNAP / "GBPJPY_H1/databanks"
    (row,) = fixed_distances(gbp / "RetestPairs/Strategy 5.17.290.sqx")
    assert (row["param"], row["value"]) == ("trailing_stop", 93)
    (row,) = fixed_distances(SNAP / "Retester/databanks/XAU Incomplete/Strategy 1.3.52.sqx")
    assert (row["param"], row["value"]) == ("FixedPips", 160)


def test_atr_sl_pt_fixture_flags_only_its_fixed_trailing() -> None:
    """Atr sl pt fixture flags only its fixed trailing."""
    assert [r["param"] for r in fixed_distances(HERE / "strategy.sqx")] == ["trailing_stop"]
