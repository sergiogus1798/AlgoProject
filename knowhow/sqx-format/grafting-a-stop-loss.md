---
q: add a stop loss to a strategy without one; graft ATR stop into sqx; SLPT.None to ATRBasedValue; StopLossCoef1 ParamTypeExitUsed; variant factory cannot add a parameter; X = 1000 probe reproduces trades
tag: 📓  date: 2026-09-26  see: sqx-format/writing-a-variant, export/sqx-atr-is-wilder
---
# A stop is grafted by two text substitutions: the entry's SLPT.None → ATRBasedValue, plus one variable
- Inside each entry's `<Param key="#StopLoss.StopLoss#">`, `SLPT.None` → the `ATRBasedValue` formula
  (`#Value#` = variable `StopLossCoef1`, `#AtrPeriod#` = literal 20); declare `StopLossCoef1` double,
  `ParamTypeExitUsed`, `makeExternal true`. The factory then moves it. `sqx.variants.build.stoploss.graft`.
- ⚠️ `#ProfitTarget.ProfitTarget#` carries the same `SLPT.None`: match the stop's key. One per entry.
- `MinMaxSLPT.*` ≠ 0 or `UseInitialSLPT` in the trading options would clamp the grafted stop.

## Evidence
- The block is what SQX itself wrote for `SL = 9.2 · ATR(20)` in `tests/fixtures/strategy.sqx`;
  `tests/test_stoploss.py` checks the graft produces it byte for byte (whitespace folded) and that
  undoing the two insertions returns the original file exactly.
- `Strategy 19.8.78` (XAUUSD M30, TestXAU_crossTF): settings carry `MinMaxSLPT.* = 0`,
  `UseInitialSLPT = false`.
- Pending: SQX loading the grafted file and the `X = 1000` retest reproducing the original trade for
  trade (`docs/manual/49-atr-calculator.md`). Until then the tag stays 📓.
