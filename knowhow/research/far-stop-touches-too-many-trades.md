---
q: Is there a far per-trade ATR stop that rarely fires on these bar-count-exit strategies?
kw: far stop 2X ATR touches too many trades, stop_percentile p90, StopLossCoef, atrCalculator breach, step 24 stop removal, Wilson upper bound 1 %, MAE/ATR p90 winners
tag: 🔬  date: 2026-10-11  see: sqx-format/grafting-a-stop-loss, export/sqx-atr-is-wilder
---
# No far stop is rare: 2·X·ATR touches 11.55 % of trades, so the per-trade stop goes
- A stop at k·X·ATR(20), X = p90 of the build winners' MAE/ATR, touches 33.0 % of trades at k=1, 18.75 % at 1.5, 11.55 % at 2
  (17,718 trades, 56 mothers, 7 projects, build+oos1; oos1 15.3 % vs build 9.3 %). No mother is below 6.2 % at k=2.
  With bar-count exits there is no «catastrophe» multiple of p90 that rarely fires.
- Decision 2026-10-11 (pre-registered in `portfolio/DECISIONS.md`): upper Wilson bound over 1 % ⇒ no per-trade stop, risk at account level.
## Evidence
Step 24 and the measuring study (`studies.closing.atrCalculator`) were deleted 2026-10-11 after the decision; the record is `docs/AgentPDFs/medicion-stop-lejano-2026-10-11.md` and the data below. Ran as `python3 -m studies.closing.atrCalculator.breach` → `AlgoData/reports/atrCalculator/breach/2026-10-11/` (`breach.md`, `touch.csv`).
Sibling mothers share trades, so the true interval is wider than Wilson's; it cannot rescue 11.5 % vs 1 %. Longs only.
- Deriving the stop from each trade's MAE reproduces SQX's real share stopped within 1 % pooled (33.0 vs 32.7 %), not its money
  (re-entries after an early exit, gap fills, stopped-trade costs are invisible): trust touch rates, never derived P/L.
- Review claims the code contradicted (do not re-raise): exposure efficiency was a ratio of returns, not of Sharpes; the conditionalMap
  volatility axis already uses build-frozen ATR terciles; the MT5 pool already stores fails and conditions; arch's SPA studentizes
  by default; steps 20-25 had no rule in `criteria.yaml`.
