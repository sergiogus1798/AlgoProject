---
q: WFM 30 cells independent? effective number of cells; share of profitable cells meaning; WFM out-of-sample curves vs buy and hold gold; WFM pass but no edge; long-only XAUUSD strategies gold beta years
tag: 🔬  date: 2026-10-01  see: conditions/wfm-acceptance, research/is-optimisation-vs-oos, export/wfm-export
---
# The 30 WFM cells are worth 1.6–3 independent curves; a WFM pass does not beat buy-and-hold
Daily OOS P/L correlates 0.56–0.79 between cells, so «28 of 30 cells profitable» is two or three
observations. Judge a WFM's OOS against the trivial alternative (holding the asset at equal risk,
the footprint random trader) and per calendar year, never by the share of cells.

## Evidence
`raw/Test_XAUUSD_donchianUpperCrossUp_H1/WFM/2026-10-01/wfm/trades.parquet`, OOS trades, 5 mothers,
2016-06 → 2026-08, each cell's daily P/L on business days (0 inside its run span):
- Effective cells (participation ratio of the 30×30 correlation eigenvalues): 1.6 (9.10.57), 2.0,
  2.5, 2.9, 7.2 (3.21.83, the losing one).
- Median-cell Sharpe 0.45–0.59 vs XAUUSD D1 buy-and-hold 0.64 over the same days; after removing the
  daily gold beta 0.36–0.46. 9.10.57 is the one SQX passes (13 of 12 needed), WFM study: perverse ρ −0.49.
- All five win 2020, 2024, 2025 and lose 2018, 2021, 2022; in 2022 0 % of cells positive for four.
- Close-date attribution understates the beta (multi-day trades). Dossier: `docs/AgentPDFs/curvas-wfm-2026-10-01.md`.
