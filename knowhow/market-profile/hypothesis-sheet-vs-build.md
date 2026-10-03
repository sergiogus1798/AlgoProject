---
q: Where is what a build produced read from when checking a hypothesis sheet?
kw: hypothesis sheet, predicted trades per year vs built, holding time, mismatch tolerance pending, sheet seal, what the build produced, Results databank trades
tag: 🔬  date: 2026-10-02  see: typed-failure-causes
---
# What a build produced is read from the Results export's in-sample trades, not from the judge's facts
A sheet predicts the MEDIAN BUILT STRATEGY (trades a year, holding hours), not the bare condition.
`studies/research/memory/sheet.py` compares it with `raw/<P>/Results/<day>/trades.parquet` (`Sample
type` starting `IS`): the autopilot's facts carry no holding time, and `is_trades_per_year` only on
scorecards after 2026-10-02. Years are the population's span, hours by the clock. The mismatch
threshold is the owner's (`studies/research/memory/config.yaml` › `sheet.tolerance`): while `pending`, the ratio is
reported and nothing is typed. A sheet edited after its proposal sealed it reads `altered`.

## Evidence
`Test_XAUUSD_emaCloseCrossUp2_H1`, Results export 2026-10-01: 300 strategies, 201,076 trades, all
`IST`; median holding per strategy 19 h (15-22). Its step-8 `hechos.parquet` has 34 keys, none on
duration and no `is_trades_per_year`. The `OOS` export of the same day holds only the 5 strategies
left after the cut, `OOS1` trades only: the wrong databank for this.
Known answer: `python3 tests/test_research_memory.py` (`test_sheet`: 10 and 30 trades a year, 10 and
30 h → median 20 and 20; predicted 50 → ratio 0.4; pending types nothing, factor 2 is a mismatch).
