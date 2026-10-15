---
q: What exits, direction and stops did the OLD 231-strategy XAUUSD corpus have (superseded by exits-and-m1-library)?
kw: XAUUSD generated strategies stop loss take profit; SLPT None; long only; ExitAfterBars 8; bar-cap vs signal-exit populations; XAUUSD in-sample window
tag: 🤔  date: 2026-10-04  see: export/exits-and-m1-library, authoring/bar-exit-ignores-task, authoring/build-doctrine-sections, research/research-lessons
---
# HISTORICAL 231-strategy XAUUSD corpus (superseded by export/exits-and-m1-library): no SL, no PT, no trailing; long-only; every exit capped at 8 bars
Owner decision 2026-10-15 (OPEN #112): old historical corpus, not reproducible; the live one is the 757-strategy `MC_Trades` of `export/exits-and-m1-library` (19.55 % `Exit Signal`, 🔬). Do not pool the two.
All 231 carry `SQ.Formulas.SLPT.None`: Build `<SLRequired>false`, `<SLATR>false`, `<PTRequired>false` (ATR machinery
configured — `MinSLATRMultiple 2`, `MaxSLATRMultiple 8`, period 20 — but toggled off). Two populations share the pool:
never pool exit statistics. **The bar-cap vs signal-exit split below is 🤔 (retagged 2026-09-29, issue 13): unstated
threshold, n=11 in one arm, duplicate trades in the 231 — redo on deduplicated trades over one window before trusting it.**

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
