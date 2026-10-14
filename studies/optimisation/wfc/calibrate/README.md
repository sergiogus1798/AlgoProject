# calibrate — how often does step 17's criterion say PASA of nothing, and NO PASA of something?

The owner's table (`../verdict/state.py`) is a rule nobody had measured. This command measures it
on families whose answer is known and writes the **register** `ledger.gate.seal` asks for before
any study opens `oos2` (`AlgoData/ledger/wfc_calibration.json`: `fecha`, `criteria_sha256`, `abre`,
`tasas`). It never reads `oos2` and never changes the criterion: when a reference rate is over its
cap the register says `abre: false` and the report says so on its first line.

```
config.yaml ─▶ families ─▶ rates ─▶ record ─▶ page
 the grid      modelling   execution  decision  the report
                           rehearsal (real batches, build → oos1)
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `__main__.py` | The command: calibrate step 17's criterion and write the register that opens the blind block. | `python3 -m studies.optimisation.wfc.calibrate [--workers 16]` | `config.yaml`, `../config.yaml`, batches with `variant_trades.parquet` → stdout, `AlgoData/ledger/wfc_calibration.{json,md}` |
| `families.py` | Synthetic families of variants whose answer is known: one common factor, own noise, a planted edge. | imported | config → `(e_is, e_oos, weeks)` |
| `page.py` | The calibration's report in Spanish: the verdict on top, then the criterion beside the one without a null on the level. | imported | table → markdown text |
| `rates.py` | Where families land in the owner's table: the criterion, and the one without a null on the level beside it. | imported | arrays → one row per scenario |
| `record.py` | The register that opens the blind block, or does not: the two reference rates against their caps. | imported | table → `wfc_calibration.json` |
| `rehearsal.py` | The criterion rehearsed on real batches with build inside and oos1 outside: legs already spent. | imported | `strategyPermutations/<P>/<S>/` → one row per batch |
| `tooltips.py` | One sentence per config.yaml knob of the calibration, for the window's configuration drawer. | imported | — |
| `config.yaml` | Families per scenario and the two caps (`ledger:` keys), the family's shape, the grid of edge sizes, costs and out-of-sample lengths, the reference cells of `abre`, the dependence sensitivity | edited, or `--set section.key=value` | — |

**It must never hold** a change to the criterion, a read of `oos2`, or a second generator of
families.

## What the numbers mean

- **False PASA** — share of no-edge families called PASA. **False NO PASA** — share of
  planted-edge families called NO PASA: the irreversible error, because a NO PASA is not
  revisited; one called LIMBO is only parked. `abre` compares, for the criterion (the level
  beating its null), the false PASA at zero mean (cap `max_false_pass`, 0.40) and the false NO PASA
  at `reference.edge` (the worse of with and without order; cap `max_false_fail`, 0.25), both at
  `reference.years_out`. The table without a null on the level stays in the report as the
  comparison column (`_sin`).
- **Measured on 2026-10-08, not registered** (`--set seed=48`, the grid as declared): false PASA
  0.03 (0.44 without the null), false NO PASA 0.13, so `abre: true`; up to 0.60 of the families
  with Sharpe 0.5 are LIMBO. The register on disk (2026-10-07: 0.02 and 0.22, `abre: true`) was
  measured for this same rule with families drawn and flipped day by day; `gate.seal` ties it
  only to the hash of criteria.yaml's entry "17". Running this command without `--set` overwrites
  it. Nobody but the owner runs it.
- **Dependence is the knob that matters for LIMBO and NO PASA with an edge.** `family.own_noise` sets how alike
  the variants are; the report prints the null deviation of rho it produces beside the 0.09–0.41
  (median 0.26) the reference run measured on real batches, and the reference cells again at two
  other values.
- The rehearsal writes no ledger row: a look needs the batch's template family, which a batch
  folder does not record. `build` and `oos1` are spent legs.
