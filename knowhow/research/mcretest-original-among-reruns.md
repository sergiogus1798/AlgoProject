---
q: Is the MC Retest's «the original is not an outlier of its re-runs» usable as a criterion?
kw: mcRetest percentil_original_estres brecha_mediana_pct_estres distancia_IQR_estres original outlier simulations median gap one-sided perturbation spread slippage stress zero-edge null not measured diagnostic
tag: 🔬  date: 2026-10-04  see: spp-decay-metrics-zero-edge-null
---
# Computed and shown, not offered: its zero-edge null needs an SQX run, and three tasks are one-sided by construction

`studies/breakage/mcRetest/model/place.py`, per task: the original's percentile among the re-runs,
the median's gap in % of the original and in IQRs. **No zero-edge null exists** — it takes an MC
Retest of zero-edge strategies, a custodian job — so the kill rule cannot be applied: diagnostics,
not in `pipeline/autopilot/offered.yaml`. Spread, slippage and stress put the original above the
median by construction: read a task against itself across strategies, never against 50.

## Evidence
`studies/breakage/mcRetest/model/place.py`, per task on Net Profit: the original's percentile among
the re-runs, the median's gap as a % of the original (missing when |original| < 0.25 IQR) and the
distance original − median in IQRs of the re-runs. Published as the table «Métricas para criterios»
of the tab «Las ocho tareas» (numeric cells, so every task is a fact) and, for the stress task, as
three `verdict.csv` columns.
**No zero-edge null exists**: it takes an MC Retest of zero-edge strategies (the monkeys of
`studies/screening/falsePositives` put through the eight MCR tasks — one custodian job). Until it
is run the kill rule cannot be applied, so the metrics are diagnostics and are not in
`pipeline/autopilot/offered.yaml`. The only reference recorded is exchangeability — an original
that were one more re-run reads a uniform percentile (5/25/50/75/95) — and three tasks break it by
construction: spread, slippage and stress draw costs mostly worse than the original's, so the
original sits above the median with no fragility at all. Read a task against itself across
strategies, never against 50.

`Trade_NIKKEI225_M30_volatilidadL`, ingest `MCR_All/2026-10-04`, 10 strategies, 200–500 re-runs per
task. Quantiles 5/25/50/75/95 across the 10 strategies:

| task | percentile of the original | median's gap, % of the original | distance, IQR |
|---|---|---|---|
| bar (control) | 0 13 46 86 95 | −19 −6 −1 0 39 | −2.6 −1.0 0.0 0.9 36.6 |
| spread | 65 67 69 70 73 | −44 −13 −5 −3 −2 | 0.23 0.32 0.36 0.44 0.48 |
| slippage | 61 66 68 69 70 | −23 −9 −3 −2 −1 | 0.23 0.30 0.35 0.37 0.39 |
| params | 38 57 77 91 93 | −173 −35 −30 −8 23 | −0.22 0.13 0.60 0.99 1.07 |
| exits | 35 47 68 83 92 | −164 −12 −7 1 14 | −0.45 −0.02 0.39 0.59 2.39 |
| ohlc | 16 33 64 88 94 | −83 −4 −1 4 32 | −0.66 −0.51 0.29 0.93 1.32 |
| stress | 63 81 86 91 95 | −316 −68 −38 −28 −23 | 0.22 0.64 0.82 0.99 1.20 |

The control (only the starting bar moves) has 3–65 distinct outcomes in 200 re-runs: its IQR
distance explodes (36.6) on a grid of a few values — the percentile is the readable one there.
Nine of the ten are FAIL on the study's own gates and the tenth INCONCLUSIVE, so these ten are no
sample of «good» values either. The owner's example (real 14,000, median 3,500–4,000) is a gap of
about −73 %, inside this range. Test: `tests/test_mcretest_place.py`.
