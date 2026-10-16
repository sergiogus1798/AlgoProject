---
q: Why did MT5 trade a ZScore strategy 20-30x less than SQX, and what makes a handle-wrapping Sq indicator read stale values?
kw: SqZScore iCustom ZScore matched share low, MT5 11 trades vs SQX 356, z[1] smaller than SQX, CopyBuffer 1 value prev_calculated, stale bar 1, handle-wrapper indicator once per bar, iStdDev population
tag: 🔬  date: 2026-10-16  see: mt5/mt5-tester-unattended
---
# SqZScore returned the bar-OPEN value for shift 1 — fixed by recomputing bar 1 on every call
- Cause: `mt5/indicators/Indicators/SqZScore.mq5` wraps iStdDev/iMA handles and, on a new bar, copied only index 0 (`copied=limit>1 ? rates_total : 1`). Bar 1 was recomputed from buffer cells last filled when it was bar 0 at its FIRST tick (price ≈ open). An EA that reads the indicator once per bar (SQX's do) saw `ZScore[1]` of the open tick: the z>2.3 signal almost never fired.
- Fix: the else-branch sets `limit=1` and copies 2 values. After it MT5 equals SQX's definition (SMA and POPULATION std, `StdDevCalculator` divides by n) to 5e-9; sample std (ddof=1) is off by up to 0.13.
- SQX ZScore itself: `(x-SMA)/popStd`, 0 before bar `Period`. Template call `iCustom(..,"SqZScore",price,Period)` matches the input order. The EA lacks `#property tester_indicator "SqZScore"` but the tester still loads the .ex5 (agent log) — not a cause.
- Suspects not audited: other Sq* wrappers that `CopyBuffer(...,0,N,..)` with N small and compute bar `shift` from it (any indicator written `copied=(limit>1 ? rates_total : 1)`). SqVortex recomputes from `prev_calculated-1` and writes its own buffers: safe. SqUlcerIndex and SqDonchianChannels read full/ price arrays: safe by code.
- After any change: `mt5.metaeditor.sqx_indicators()` (terminal closed) reinstalls and recompiles.

## Evidence
2026-10-16, FTMO-Server4 USDJPY H1 2025-01-02..03-31, every_tick, probe EA logging `iCustom(SqZScore,close,13)` at each new bar vs pandas `(c-SMA13)/std(ddof=0)`. Before: max |diff| 4.68, median 0.39, z>2.3 on 0.07 % of bars (reference 2.7 %). After: max |diff| 5e-9. 2025-01-02 20:00: before 1.885 (stale), after 1.685734 = SQX definition 1.685734.
