# cscv — step 18: does choosing the best variant of the past serve outside?

The paper's method (Bailey, Borwein, López de Prado, Zhu, «The Probability of Backtest
Overfitting») on one mother's variant batch, with the margin of error the paper does not bring.
The owner's specification is `criterios-implementados-2026-10-12` (2026-10-07). It can discard and
never confirms: PASA means «no descarta».

```
python3 -m studies.optimisation.cscv.report --work <batch> [<batch> ...] --family <f> [--set k=v]
```

Several batches share one queue of processes. Each writes, in its own `estudios/`: `distribuciones.parquet` (the nulls behind `pbo_p`, `beta_p`, the gross PBO and `p_perdida`), `cscv.json`
(small: the contract, `facts`, `rendimiento`), `cscv.html`, `cscv.md`, and the detail nobody loads
to decide — `cscv_particiones.parquet` (one row per partition) and `cscv_sorteos.parquet` (one
per draw). A batch without `variant_trades.parquet` stops the command with what to do.

| file | what it does | in → out |
|---|---|---|
| `config.yaml` | Every knob, commented; the cuts are `ledger:` rows | — |
| `tooltips.py` | One Spanish sentence per knob, for the window | — |
| `words.py` | The Spanish the page is read with: labels, meanings, one line per statistic, glossary | — |
| `many.py` | Screens each batch's panel, runs the one queue, reads the facts and the warnings | batches, cfg → per-mother dict, perf |
| `contract.py` | The four tabs and the verdict as contract blocks | one mother → tabs |
| `report.py` | The command: door, panels, queue, files, ledger look | folders → `estudios/cscv.*` |
| `inputs/` | Config, and trades → weekly cells → screened panel | [README](inputs/README.md) |
| `measure/` | The CSCV, its outputs, the null, the queue | [README](measure/README.md) |
| `verdict/` | The facts and the state | [README](verdict/README.md) |

## What is computed

- **Cells**: weekly excess of each variant from its trades (`engines.weekly.panel`), net; gross
  too, only for «orden estable». Cached beside the batch as `cscv_weekly.parquet`.
- **Panel**: controls out, exact duplicates out (`engines.variants.fingerprint`, share annotated),
  floors over the whole history, the mother always in.
- **CSCV**: 16 blocks of near-equal length (`np.array_split`; no row is dropped), 12,870
  partitions, the best weekly Sharpe inside scored outside.
- **Four outputs**: PBO, the degradation line (β, adjusted R²), probability of loss, stochastic
  dominance against the out-of-sample Sharpe of ALL variants in all partitions. Plus the Sharpe
  haircut HC = 1 − median out / median in, the selection frequency and the mother's own reading.
- **Null**: columns standardised, all given the same mean, weeks redrawn by stationary bootstrap
  (the same rows for every variant), the whole CSCV per draw; on net and on gross.
- **Power**: an annual Sharpe δ planted in 10 % of the equalised columns (redrawn each draw);
  the share of draws whose PBO falls under the null's p5.

## The state

| state | when |
|---|---|
| NO PASA | P(loss) ≥ `state.p_perdida_fail`, or PBO ≥ the p95 of its own null |
| LIMBO | P(loss) > the p`state.p_perdida_null_pct` (95) of its own null's P(loss) — `p_perdida_sobre_p95` — or fewer than `panel.min_variants` variants |
| PASA — no descarta | otherwise; «orden estable» added when PBO ≤ the null's p5 on net AND gross |

LIMBO is read against the null (owner, 2026-10-08; the fixed 0.25 cut is gone). The null's
columns all carry the panel's median Sharpe, usually positive, so «above the null's p95» means:
the pick loses outside more often than 95 % of the picks among variants that are ALL worth the
panel's median — it says choosing lands on something worse than the median variant, and says
nothing about the level of the loss, which the 0.5 cut reads.

Measured (2026-10-08, 60 variants × 400 weeks, 100 draws, 300-400 panels each): the rule is
conservative, never above its 5 %. The null is centred on the panel's OWN sample median and then
redrawn, so the real loss sits at the centre of its null, and whatever the variants share moves
both together.

| panel | over its null's p95 | LIMBO | NO PASA |
|---|---|---|---|
| no edge, independent columns, weekly Sharpe 0.10 | 5.2 % ± 1.1 | 3.0 % ± 0.9 | 6.2 % |
| no edge, independent, 0.03 (null p95 0.57 > 0.5) | 6.7 % ± 1.4 | 0 % | 14.7 % |
| no edge, columns correlated 0.2, 0.10 | 0.5 % ± 0.4 | 0 % | 6.0 % |
| no edge, correlated 0.6, 0.03 / 0.10 / 0.15 | 0 % | 0 % | 29.3 % / 7.0 % / 7.0 % |
| one planted best variant (+0.15 / +0.25 weekly), correlated 0.6 | 0 % | 0 % | 1.7 % / 0 % |

Variants of one mother are correlated, so on real batches expect LIMBO from this rule close to
never; where the null's p95 is at or over 0.5 it cannot fire at all (the 0.5 cut fires first).
The NO PASA column at 0.03 is the 0.5 cut on panels with nothing to choose and a low Sharpe.

## Readings chosen where the specification leaves room (questions open with the owner)

- **«The same mean m»**: every equalised column gets the panel's **median weekly Sharpe** as its
  mean, in its own deviation units. The common deviation s cancels in a Sharpe, so it is 1.
- **First-order dominance** takes `dominance.tolerance` (0.01): the chosen values are a subset
  of all the values, so the strict version fails by construction just under the maximum. The
  largest gap is annotated (`dominancia.brecha`). Second order is strict.
- **`pbo_p`** is the lower tail (share of null draws at or under the real PBO, the real one
  counted); `pbo_p_mas` is the upper one.
- **HC** is NaN when the median Sharpe inside is not positive.
- The null on gross is a fifth kind of draw: 5 × `null.draws` CSCVs per mother, not 4.

## Cost (measured 2026-10-07, 48 physical cores, machine at load 105)

| variants | draws | wall | CPU |
|---|---|---|---|
| 300 | 200 | 3.5 s | 72 s |
| 1,000 | 200 | 8.9 s | 243 s |
| 300 | 1,000 | 13.5 s | 349 s |
| 1,000 | 1,000 | 40.5 s | 1,195 s |

784 weeks; 107 MB at most per process. One CSCV of 1,000 variants takes 0.18 s on one thread.
One process against 48: ×14 to ×21 on 240 CSCVs of 300 variants. `core.fanout` never uses more
than the physical cores, so `perf.workers: 96` runs 48.

## Tests

`python3 tests/test_cscv.py` — the frozen numbers of the implementation this replaced, the
row-by-row reference, the seesaw, dominance by hand, reproducibility with 1, 8 and 96 processes,
the null's band, power, scaling and the state's table; `python3 tests/test_cscv_batch.py` — a
synthetic batch end to end, synthetic trades into cells, the loss against its null's percentile
by hand and how often no edge is over it. No batch on disk carries `variant_trades.parquet` yet, so nothing trade-based
has run on a real mother.
