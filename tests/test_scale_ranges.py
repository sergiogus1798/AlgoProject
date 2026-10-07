#!/usr/bin/env python3
"""Cross TF coefficients (encargo 47 part F, owner 2026-10-07): a coefficient that multiplies a
per-bar measure is divided by the measured ATR ratio c; one over a window, a level and a ratio
stay; one nobody ruled flags the sibling."""

import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.assetdata import doctrine
from sqx.variants import lengths, ranges, scale
from sqx.variants.build import rewrite

# (variable, type, value, SQX paramType, block, parameter key)
VARIABLES = [
    ("RSIPeriod1", "int", "41", "ParamTypePeriod", "RSIHigher", "Period"),
    ("RSILevel1", "double", "55", "ParamTypeConstant", "RSIHigher", "Level"),
    ("CBlock_PMaxInt21", "int", "10", "ParamTypeOtherParam", "CBlock_PMaxFlipUp", "Int2"),
    ("CBlock_PMaxDbl31", "double", "3", "ParamTypeOtherParam", "CBlock_PMaxFlipUp", "Double3"),
    ("CBlock_BBDbl31", "double", "0.8", "ParamTypeOtherParam", "CBlock_BBBreakoutUp", "Double3"),
    ("CBlock_RankDbl31", "double", "61", "ParamTypeOtherParam", "CBlock_ATRRankHighVol",
     "Double3"),
    ("SuperTrendATRMult1", "double", "5", "ParamTypeOtherParam", "SuperTrendUPTrend", "ATRMult"),
    ("VWAPFstStdDevMlt1", "double", "1.7", "ParamTypePeriod",
     "FastAnchoredVWAPAboveSlowAnchoredVWAP", "FastStdDevMult"),
]
LOOSE = [
    ("CBlock_CandleDbl21", "double", "1.5", "ParamTypeOtherParam", "CBlock_CandleBreakoutLong",
     "Double2"),
    ("CBlock_NobodyDbl11", "double", "2", "ParamTypeOtherParam", "CBlock_NobodyListedThis",
     "Double1"),
    ("KalmanDecay1", "double", "0.5", "ParamTypeOtherParam", "KalmanFilter", "Decay"),
]
STOP = ('<Item key="EnterAtMarket"><Param key="#StopLoss.StopLoss#">'
        '<Formula key="SQ.Formulas.SLPT.ATRBasedValue">'
        '<Param key="#Value#" controlType="jspinnerVar" type="double" variable="true">'
        'StopLossCoef1</Param>'
        '<Param key="#AtrPeriod#" controlType="jspinnerVar" type="int">20</Param></Formula></Param>'
        '<Param key="#ProfitTarget.ProfitTarget#"><Formula key="SQ.Formulas.SLPT.ATRBasedValue">'
        '<Param key="#Value#" controlType="jspinnerVar" type="double">4</Param>'
        '<Param key="#AtrPeriod#" controlType="jspinnerVar" type="int">20</Param></Formula></Param>'
        '</Item>')


def portfolio(variables: list[tuple]) -> str:
    """A strategy_Portfolio.xml reduced to what the scaling reads, with an ATR stop and target."""
    variables = [*variables, ("StopLossCoef1", "double", "2", "ParamTypeExitUsed", "", "")]
    declared = "".join(f"<variable><id>{n}</id><name>{n}</name><type>{t}</type><value>{v}</value>"
                       f"<paramType>{k}</paramType></variable>" for n, t, v, k, _, _ in variables)
    rules = "".join(f'<Item key="{b}"><Param key="#{p}#" type="{t}" variable="true">{n}</Param>'
                    "</Item>" for n, t, _, _, b, p in variables if b)
    return (f'<?xml version="1.0" encoding="UTF-8"?><StrategyFile><Variables>{declared}'
            f"</Variables><Rules>{rules}{STOP}</Rules></StrategyFile>")


def sibling(target: str, c: float | None, variables: list[tuple] = VARIABLES) -> dict:
    """The manifest row `scale.sibling` writes, M30 to `target`, with the file's text and values."""
    with tempfile.TemporaryDirectory() as tmp:
        mother = Path(tmp) / "Mother.sqx"
        with zipfile.ZipFile(mother, "w") as z:
            z.writestr("META-INF/MANIFEST.MF", "")
            z.writestr(rewrite.SETTINGS, '<ResultsGroup ResultName="Mother"><StrategyName '
                                         'type="String">Mother</StrategyName></ResultsGroup>')
            z.writestr(rewrite.PORTFOLIO, portfolio(variables))
        row = scale.sibling(mother, Path(tmp), "M30", target, scale.knobs(), 0, c)
        text = rewrite.members(Path(row["path"]))[rewrite.PORTFOLIO].decode()
    return row | {"text": text, "written": rewrite.values(text)}


def walk(sigma: float, seed: int) -> pd.DataFrame:
    """Bars of a random walk whose per-bar volatility is `sigma`."""
    rng = np.random.default_rng(seed)
    step = rng.normal(0, sigma, 200_000)
    close = 10_000 + np.cumsum(step)
    wick = np.abs(rng.normal(0, sigma / 2, (2, len(step))))
    return pd.DataFrame({"High": np.maximum(close, close - step) + wick[0],
                         "Low": np.minimum(close, close - step) - wick[1], "Close": close})


def test_c_is_the_per_bar_volatility_ratio() -> None:
    """Bars 1.4 times more volatile have an ATR 1.4 times bigger: c = k within 1 %."""
    k = 1.4
    c = ranges.ratio(walk(10, 1), walk(10 * k, 2), 20, 20)
    assert abs(c / k - 1) < 0.01


def test_m15_doubles_every_period_exactly() -> None:
    """M30 to M15: 41 is 82, the stop's literal ATR(20) is ATR(40), no rounding, no clamp."""
    got = sibling("M15", 0.7)
    assert (got["written"]["RSIPeriod1"], got["written"]["CBlock_PMaxInt21"]) == ("82", "20")
    assert got["text"].count('type="int">40</Param>') == 2 and 'type="int">20<' not in got["text"]
    assert got["max_rounding_shift"] == 0 and not got["clamped"] and got["n_scaled"] == 4


def test_bar_divides_by_c_and_window_and_other_stay() -> None:
    """PMax's and SuperTrend's ATR multiple, the stop's coefficient and the target's literal
    are divided by c; the Bollinger deviation, the VWAP's (typed a period by SQX), the rank
    level and the RSI level are not."""
    got = sibling("H1", 1.25)
    w = got["written"]
    assert [float(w[n]) for n in ("CBlock_PMaxDbl31", "SuperTrendATRMult1", "StopLossCoef1")] == \
        [2.4, 4.0, 1.6]
    assert 'type="double">3.2</Param>' in got["text"]            # the target's literal 4
    assert [w[n] for n in ("CBlock_BBDbl31", "VWAPFstStdDevMlt1", "CBlock_RankDbl31",
                           "RSILevel1")] == ["0.8", "1.7", "61", "55"]
    assert (got["n_coef_scaled"], got["atr_ratio"], got["unverified"]) == (4, 1.25, "")
    assert got["was_StopLossCoef1"] == 2.0 and got["param_StopLossCoef1"] == 1.6


def test_what_nobody_ruled_flags_the_sibling() -> None:
    """A row ruled unverified, a custom block's unlisted double and an unruled built-in
    coefficient stay as they were and are named; so is every per-bar coefficient when c
    could not be measured."""
    got = sibling("H1", 1.25, VARIABLES + LOOSE)
    assert got["unverified"] == "CBlock_CandleDbl21,CBlock_NobodyDbl11,KalmanDecay1"
    assert [got["written"][n] for n, *_ in LOOSE] == ["1.5", "2", "0.5"]
    blind = sibling("H1", None)
    assert blind["unverified"] == ("CBlock_PMaxDbl31,SuperTrendATRMult1,StopLossCoef1,"
                                   + ranges.LITERAL)
    assert blind["n_coef_scaled"] == 0 and blind["written"]["StopLossCoef1"] == "2"


def test_the_table_rules_every_custom_block_and_the_doctrine_asks_for_m15() -> None:
    """A ruling is one of four words, every custom block `lengths.yaml` lists has a row, every
    double it rules a non-length is ruled here, and an M30 mother gets M15, H1 and H4."""
    table, known = ranges.table(), lengths.table()
    words = {ranges.BAR, ranges.WINDOW, ranges.OTHER, ranges.UNVERIFIED}
    assert {r["measure"] for r in table[ranges.BUILTIN]} <= words
    assert {m for b, row in table.items() if b != ranges.BUILTIN for m in row.values()} <= words
    assert set(known) <= set(table)
    assert all(p in table[b] for b, row in known.items() for p, r in row.items()
               if r != "length" and not p.startswith("Int"))
    assert doctrine()["crosstf"]["timeframes"]["M30"] == ["M15", "H1", "H4"]


if __name__ == "__main__":
    test_c_is_the_per_bar_volatility_ratio()
    test_m15_doubles_every_period_exactly()
    test_bar_divides_by_c_and_window_and_other_stay()
    test_what_nobody_ruled_flags_the_sibling()
    test_the_table_rules_every_custom_block_and_the_doctrine_asks_for_m15()
    print("ok")
