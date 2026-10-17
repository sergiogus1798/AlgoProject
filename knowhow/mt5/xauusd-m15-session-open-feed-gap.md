---
q: Why do XAUUSD M15 step-26 checks fail on FTMO and Hantec while JPY crosses H1 pass (matched share 0.85, entries missed at server hours 00-04)?
kw: step 26 gold fails, XAUUSD M15 matched share 0.85, row 1 below 0.90, EhlersMAMA unmatched trades, session open feed gap, hour 1 bar open differs, rows 3b 4 5 fail one lot gold, MT5 FTMO vs Hantec disagree
tag: 🤔  date: 2026-10-17  see: mt5/sqzscore-stale-previous-bar, mt5/mt5-verify-clock-zones
---
# Gold M15 fails step 26 on a feed gap at the session open, amplified by marginal rising-chains and by 1-lot dollars
- 🔬 Not spread: SQX's entry times are identical across the FTMO and Hantec runs (same data, different cost), so the median-spread change cannot move an entry.
- 🔬 Not a clock shift or a one-bar lag: 92-97 % of matched pairs enter at the same minute; unmatched entries are ~1 day from any entry of the other side. 25-40 % of them are position-blocking cascades (the other side was already in a trade).
- 🔬 Not a history-start seed: miss rate is flat by year (10-20 %), months without bars are already excluded.
- 🔬 MT5 FTMO vs MT5 Hantec agree on only 77-94 % of entry minutes, no better than either against SQX: the residue is feed-noise-driven, not one deterministic MT5 indicator bug.
- 🔬 SQX's XAUUSD feed (Dukascopy) vs FTMO's H1 bars (2024-26): mid (H+L)/2 differs 0.11-0.14 USD at most hours but **hour 01 (first bar after the daily break) 0.85 and hour 23 0.36** (open differs by median 1.6 USD, p90 8.5 at 01:00; SQX low lower by 1.7 on average). Strategies whose entry is a rising-chain of 8-9 bars of a (H+L)/2 filter (SqEhlersMotherOfAdaptiveMovingAverages, three of the five) miss **32 %** of entries at server hours 00-04 against 7-12 % at other hours; strategies on SqZScore / SqBHErgodic miss 4-7 % at any hour.
- 🔬 Rows 3b/4/5 are in % of a 100k account at 1 lot of gold (1 USD = 100 USD of P&L, a trade is ~1.5-2 % of the account): one unmatched trade moves the worst day by ~2 pp, so they fail with any residue, while row 2 (R) passes.
- 🤔 Ranked: (1) session-open feed gap into marginal chain signals; (2) 1-lot dollar scale on rows 3b/4/5; (3) the MQL port of the MAMA/Hilbert differs from SQX's block (`mt5/indicators/Indicators/SqEhlersMotherOfAdaptiveMovingAverages.mq5` radians for deltaPhase with clamp 1, `NormalizeDouble(q1/i1,6)`) — not testable offline; (4) a stale-bar bug like SqZScore: not seen, the new-bar branches compute bar 1 from final data (`...MAMA.mq5` limit==1, `SqEhlersHilbertTransform.mq5:97`).
- Smallest experiment (MT5 free): probe EA on FTMO XAUUSD M15, one month, logging at each new bar CopyRates(1) H/L and iCustom MAMA/FAMA at shift 1-2; recompute offline on those same bars. Equal to 1e-9 = indicator exact (hypothesis 3/4 out, feed confirmed); different = port bug.

## Evidence
Runs `AlgoData/mt5/verify/20261017-{130618,131845,132607,133226,133825}_strategy`, trades in `sqx/<firm>/trades.parquet` and `AlgoData/mt5/tests/V<run>lot_strategy_<firm>_*/trades.parquet`; bars `AlgoData/bars/XAUUSD_M1/M1.parquet` vs `AlgoData/mt5/bars/XAUUSD/H1_2022-06-01_2026-10-08.parquet`.
