---
q: Why does the anomalous-duration cut of the deep-MAE screen mark nothing on a real population?
kw: maeDepth anomalous trades zero; duration mean plus 2.5 sd; Exit After X Bars; deep MAE recovered share; criba MAE profundo
tag: 🔬  date: 2026-10-04  see: export/sqx-atr-is-wilder, research/research-lessons
---
# mean + 2.5 sd of a strategy's durations marks no trade on exit-after-X-bars populations
- `studies/screening/maeDepth` flags a trade anomalous when MAE >= k ATR and its duration (in bars) is
  >= mean + 2.5 sd of that strategy's durations in that segment (owner, 2026-09-28). On populations whose
  strategies exit after X bars or at the end of Friday, durations are bounded and bimodal: the cut sat above
  every trade, so `anom*` counts are 0. The deep-but-not-anomalous reading (`prof*`) is what carries signal.
- Same population, deep (>= 3 ATR) trades are 26 % of build trades and the recovered ones give 33 % of the net
  on average (10-52 %); in oos1 they are 24 % and give 8 %. Those strategies lived on recovered deep trades in build.
- The cut is not changed by the code: it is shown per strategy and segment, and the owner decides.

## Evidence
- `python3 -m studies.screening.maeDepth.report --project Test_USDJPY_donchianUpperCrossUp_M30 --databank Results
  --feed USDJPY_M1`: 21 strategies, 34,118 trades, 2 s; `n_long` 0 in every strategy and segment. Three XAUUSD
  Test_ harvests (GuiChain M30, donchian H1, timeRangeBreakout2 M30): the same, `n_long` 0.
