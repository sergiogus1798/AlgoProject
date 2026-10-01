---
q: WFM 30 cells independent? original strategy vs buy and hold, which curve represents the strategy, main backtest Sample type IST; effective number of cells; share of profitable cells meaning; WFM out-of-sample curves vs buy and hold gold; WFM pass but no edge; long-only XAUUSD strategies gold beta years
tag: 🔬  date: 2026-10-01  see: conditions/wfm-acceptance, research/is-optimisation-vs-oos, export/wfm-export
---
# The 30 WFM cells are worth 1.6–3 independent curves; a WFM pass does not beat buy-and-hold
Daily OOS P/L correlates 0.56–0.79 between cells, so «28 of 30 cells profitable» is two or three
observations. Judge a WFM's OOS against the trivial alternative (holding the asset at equal risk,
the footprint random trader) and per calendar year, never by the share of cells — and with the
**original** strategy's curve over `oos2` only, not a chosen cell (choosing one of
30 after seeing them is selection on the judged sample). The WFM main block is tagged `IST`
throughout: take the OOS days from `_policy.yaml`. Built: tab «Contra el activo y el azar».

## Evidence
`raw/Test_XAUUSD_donchianUpperCrossUp_H1/WFM/2026-10-01/wfm/trades.parquet`, OOS trades, 5 mothers,
2016-06 → 2026-08, each cell's daily P/L on business days (0 inside its run span):
- Effective cells (participation ratio of the 30×30 correlation eigenvalues): 1.6 (9.10.57), 2.0,
  2.5, 2.9, 7.2 (3.21.83, the losing one).
- Median-cell Sharpe 0.45–0.59 vs XAUUSD D1 buy-and-hold 0.64 over the same days; after removing the
  daily gold beta 0.36–0.46. 9.10.57 is the one SQX passes (13 of 12 needed), WFM study: perverse ρ −0.49.
- All five win 2020, 2024, 2025 and lose 2018, 2021, 2022; in 2022 0 % of cells positive for four.
- Original, marked to D1 close, **oos2 only** (2023-01-03 → 2026-08-28, 944 days — oos1 screened
  the population): Sharpe 0.62…1.20 vs gold 1.31; every gap interval holds 0 (≈ 2 Sharpe units
  wide: 3.7 years cannot separate 1.0 from 1.3); Sharpe without gold 0.19…0.82, intervals hold 0.
  On oos1 all five lose (−0.53…−0.17 vs 0.52) — odd for a population screened there; unchecked.
- Same window, 10,000 `timing` monkeys (reconcile 0.9999): p on Sharpe 0.016–0.16, two of five
  ≤ 0.05 (9.10.57, 20.25.72) before any correction for five tests; on net profit p 0.25–0.43 —
  a long monkey in rising gold earns too; the strategies are calmer (DD p 0.001–0.07), not richer.
- Close-date attribution understates the beta (multi-day trades). Dossier: `docs/AgentPDFs/curvas-wfm-2026-10-01.md`.
