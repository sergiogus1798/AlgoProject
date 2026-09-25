---
q: XAUUSD generated strategies stop loss take profit; SLPT None; long only; ExitAfterBars 8; bar-cap vs signal-exit populations; XAUUSD in-sample window
tag: 🔬  date: 2026-09-04  see: authoring/bar-exit-ignores-task, authoring/build-doctrine-sections
---
# The XAUUSD corpus has no SL, no PT, no trailing; long-only; every exit capped at 8 bars
All 231 carry `SQ.Formulas.SLPT.None`: Build task `<SLRequired>false`, `<SLATR>false`, `<PTRequired>false`
(ATR machinery configured — `MinSLATRMultiple 2`, `MaxSLATRMultiple 8`, period 20 — but toggled off).
Two structurally different populations share the pool: never pool exit statistics.

## Evidence
- `<MarketSides type="long">`: 231/231 long entry, 0 short.
- `ExitAfterBars` = 8 on all 231 though the generator range is 5–20.
- ~129 bar-cap strategies (100 % exits at the 8-bar cap, median MAE 1.37×ATR) vs ~11 signal-exit
  (rule exit after 1–3 bars, median MAE 0.95×ATR, some near 0.01).
- IS window `2008.01.01–2017.12.31` (`<Setup dateFrom= dateTo=>` in `Build-Task3.xml`).
