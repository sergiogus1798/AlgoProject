---
q: XAUUSD generated strategies stop loss take profit; SLPT None; long only; ExitAfterBars 8; bar-cap vs signal-exit populations; XAUUSD in-sample window
tag: 🤔  date: 2026-09-04  see: authoring/bar-exit-ignores-task, authoring/build-doctrine-sections, research/research-lessons
---
# The XAUUSD corpus has no SL, no PT, no trailing; long-only; every exit capped at 8 bars
All 231 carry `SQ.Formulas.SLPT.None`: Build task `<SLRequired>false`, `<SLATR>false`, `<PTRequired>false`
(ATR machinery configured — `MinSLATRMultiple 2`, `MaxSLATRMultiple 8`, period 20 — but toggled off).
Two structurally different populations share the pool: never pool exit statistics. **The bar-cap
vs signal-exit split below is 🤔, not 🔬 (retagged 2026-09-29, issue 13): unstated threshold,
n=11 for one arm, and the 231 denominator itself carries the corpus's own duplicate-trade problem —
redo on deduplicated trade lists over one window before trusting the comparison.** Every figure
here is from the old project's export and cannot be reproduced from today's data root (OPEN §12).

## Evidence
- `<MarketSides type="long">`: 231/231 long entry, 0 short.
- `ExitAfterBars` = 8 on all 231 though the generator range is 5–20.
- ~129 bar-cap strategies (100 % exits at the 8-bar cap, median MAE 1.37×ATR) vs ~11 signal-exit
  (rule exit after 1–3 bars, median MAE 0.95×ATR, some near 0.01) — **129 + 11 = 140 of 231,
  leaving 91 (39 %) unclassified; the rule that sorts a strategy into either bucket was never
  written down.** The MAE comparison rests on **n = 11** for the signal-exit side.
- Denominator: the raw 231, which `knowhow/export/what-a-project-stores.md` records as holding
  **45 byte-identical trade lists under different `.sqx` hashes** — the corpus's own instance of
  `studies/CLAUDE.md`'s first trap. The 129/11/91 split above was counted on the 231 names, not on
  the distinct trade lists beneath them, so its proportions are not safe as stated.
- The pool mixes retest windows: 46 of 231 cover only 2018–2023, the rest the full IS window below.
- IS window `2008.01.01–2017.12.31` (`<Setup dateFrom= dateTo=>` in `Build-Task3.xml`).
