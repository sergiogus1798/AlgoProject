# cscv/verdict — what the numbers mean

| file | what it does | in → out |
|---|---|---|
| `state.py` | Step 18's facts and its state: the real CSCV read against its null, and the cut of the proposal. | readings, draws, counts, cfg → facts |

`cscv.p_perdida`, `cscv.pbo_sobre_p95` and `cscv.p_perdida_sobre_p95` decide (the autopilot's
`criteria.yaml` reads the first and the last by these names); everything else is annotated. The
cut and the percentile come from the config (`ledger:` rows). The PBO's cut is the p95 of its own
null and has no number: a fixed 0.5 misreads a statistic whose no-edge deviation is 0.11 to 0.14.
`p_perdida_sobre_p95` is strict (>): a pick that never loses is not over a null that never loses.

**Must never hold**: a computation over the panel, an import of `measure/`.
