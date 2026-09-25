# studies/optimisation/cloud — is the chosen point a lucky spike, and does its cloud hold up?

One study, one folder. It reads a batch of fabricated variants that has already been retested —
contracts C3 (`metrics.parquet`) and the harvested `equity.parquet` — and asks four questions that
`walkForwardCorrelation` does not: **where theta-zero sits among its own neighbours, who actually
moves the result, whether the surface is a surface at all, and whether its shape survives being cut
into periods.** It never talks to SQX and it never runs a backtest.

```
config.yaml ─▶ inputs ─▶ model ─▶ measure ─▶ verdict ─▶ contract
 every knob    the cloud  the       the         what it    the
               and the    geometry  per-period  means      panel
               curves     and the   and the
                          surrogate ensemble
```

| folder | the question it answers | read its README before |
|---|---|---|
| `inputs/` | which variants may be described, and over what history? | touching a filter or the reserved-segment cut |
| `model/` | what shape is the cloud, and who gives it that shape? | changing the neighbourhood metric or the surrogate |
| `measure/` | what are the per-period and per-ensemble numbers? | touching the period metric or how members are picked |
| `verdict/` | what does each of them mean? | moving a threshold |

| file | what it does | run it | in → out |
|---|---|---|---|
| `one.py` | Every measurement of one batch and its four readings, as the contract's data the window paints | imported — the window calls it | batch → result |
| `contract.py` | The four tabs — A1, A2 and A3, B2, C1 — each with its readings | imported | numbers → tabs |
| `report.py` | **The command**: prints the result and writes `cloud.json`, `cloud.html` and `cloud.md` into the batch; `--out` also writes the numbers alone | `python3 -m studies.optimisation.cloud.report --work <dir>` | batch → four readings |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported | — |
| `config.yaml` | Every tunable, grouped by the layer that reads it | edited, or `--set section.key=value` | — |

Manual page, in Spanish: `docs/manual/39-nube-de-parametros.md`.

🔬 **What it costs**, measured 2026-09-24 on `Strategy 17.9.39` (998 variants after filtering, 3,925
days, 7 live parameters): **1.9 s wall, 410 MB peak RSS**. The whole batch is read into memory at
once because it fits; the Sobol indices are 2¹² × (k+2) surrogate evaluations, which is arithmetic
and rounds to nothing beside the parquet reads.

## Diagnosis, never selection

**The cloning is itself a search.** Two thousand clones is a larger optimisation, not a free
robustness check, and if any clone were kept *because it scored best* the result would be a more
overfit strategy with a smaller effective sample. So nothing here returns a better variant. The
readings measure rank, plateau size, sensitivity, smoothness, persistence and drift; moving
theta-zero is the owner's decision, logged, and revalidated on data this study never touched.

## The four things this module exists to get right

**`oos2` is a one-way door, and a per-period heatmap would walk through it.** `_policy.yaml`
reserves that segment for the walk-forward correlation and the walk-forward matrix. Every look
spends it, so `inputs.cloud.before_reserved` cuts the curves at its first day whatever the batch was
retested over, and the report says how many days it dropped.

**Distance is measured in level steps, not per cent.** The cloud is discrete and was designed in
levels (`sqx/variants/design/`), so "±20 %" means something different for a bar count of 3 and a
period of 67, while "two steps" means the same thing for both.

**A filter can flatten a parameter, and that is a finding.** 🔬 Measured 2026-09-24 on
`Strategy 17.9.39`: dropping the canaries and every variant under 30 trades leaves `DICrossShift1`
with a single value. Everything but shift 1 barely trades, so that parameter does not choose between
good and bad — it chooses between trading and not. It is named in the report and left out of the
fit, where it would otherwise be handed a sensitivity index of zero it did not earn.

**The Sobol indices are computed on the surrogate, and they inherit its roughness.** The design this
project fabricates is stratified, not a Saltelli design, so estimating indices directly would cost
N(k+2) fresh backtests. On the surrogate they cost arithmetic — and an index read off a model with a
low r² describes a shape the data only half supports, which is why the r² is printed beside them.

## What it does not tell you

- **Nothing about a market it was not run on.** The multi-market surfaces (A4) and the cross-market
  transfer of the optimal region (B3) need a variant retest carrying the cross-checks of
  `assets/_markets.yaml`. `sqx.variants.equity` already writes `equity_markets.parquet` when they
  are there; no batch on this install has them yet. `docs/encargos/15-superficies-multimercado.md`.
- **Nothing about rules**, only about parameter values. Ablation and inversion need the strategy's
  logic edited, not its variables: `docs/encargos/12-tests-estructurales.md`.
- **`active` is days, not trades.** A per-period trade count needs the trade export, ninety minutes
  against this file's 1.5 seconds. Periods below `min_active_days` are dropped rather than read.
