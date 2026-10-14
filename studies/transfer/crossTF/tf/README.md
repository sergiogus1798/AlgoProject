# crossTF/tf — «is the edge an isolated peak on its timeframe?»: T0 to T4

The step-12 redesign (encargo 47, part K; spec `criterios-implementados-2026-10-12`
§2, §5, §6). A mother and all her period-rescaled siblings go through the **same** random runs —
one whole-week shift per calendar year and run, never across the build / oos1 frontier — priced by
the one repricer at the doctrine's size, in R. Written **beside** the old reading (`z_new`), which
still judges until the owner cuts: `tf_siblings.parquet` and `tf_mothers.csv` in the run's folder.

**Imports from:** `core/`, `engines/market/reprice`, `studies/screening/analysis/centred`
(overdispersion) and `studies/transfer/crossmarket/travel` (`cells`, `shift`, `sizing`, `tensor`,
`stat`, `validity.card`) — a timeframe takes the place of a market in travel's tensor; nothing of
travel is copied or edited.
**Must not contain:** a threshold (all in `config.yaml` › `tf:`), a call to SQX, a rule of
`criteria.yaml`, anything of the old reading (`cells.py`, `verdict.py`).

| file | what it does | run it | in → out |
|---|---|---|---|
| `inputs.py` | What the T0-T4 reading is run on: the siblings made, the oos1 trades the study already loaded, and the build trades when phase 2 ran. | imported | plan, packed trades, batch folder → frames |
| `null.py` | The joint random runs of one mother and her siblings in one window, and the three measures read off them: e, z of a total, z of the difference. | imported | trades per timeframe, bars, costs → cells, e, z |
| `rules.py` | T0 to T4 and the verdict per mother: from measured siblings to pass, limbo or fail, with why. | imported | measured columns → pass / limbo / fail, why |
| `run.py` | The runner of the T0-T4 reading: what the study loaded in, `tf_siblings.parquet` and `tf_mothers.csv` out, beside the old reading. | imported | `many.load` → `tf_siblings.parquet`, `tf_mothers.csv`, `distribuciones.parquet` |
| `table.py` | The siblings table and the mothers table: every sibling measured in each window, then judged. | imported | made, trades, bars → the two tables |

## What is measured where

| column | window | read on | meaning |
|---|---|---|---|
| `e_*`, `ret`, `ret_build` | each | net R | (T_real − mean T_random) / n; `ret` = e_sibling / e_mother, empty unless e_mother > 0 |
| `z_delta` | oos1 | `tf.runs.judge_on` | e_mother − e_sibling against the same difference in every joint run |
| `z_build` | build | `tf.runs.judge_on` | the sibling's total against her own random runs |
| `z_frec` | build + oos1 | counts | ln(n_sibling / n_mother) − the batch's median for that timeframe, over √(φ (1/n_s + 1/n_m)) |
| `overlap_*` | each | entry times | share of the sibling's entries under one MOTHER bar from one of hers |

A state with no data is `limbo` and its `<test>_why` says what is missing (`unverified`, `clamped`,
`rounding_shift`, `few_trades`, `mother_few_trades`, `mother_e_not_positive`, `no_build_data`,
`population_below_min`, `no_cost_card`, `cost_card_pending: …`); `""` means it was measured.

## Open readings (owner's call, encargo 47)

- **R is each timeframe's own.** Lots follow the doctrine on the sibling's bars, so 1 R is 4 ATR
  of *her* timeframe: a sibling earning the same price per trade as an M30 mother reads `ret` ≈ 0.7
  on H1 and ≈ 1.4 on M15. Every z is scale-free; `ret` and its 0.5 / 0.25 thresholds are not.
- **A lone measured neighbour that fails T2a or T2b** is limbo with `t2a_lone_fail` /
  `t2b_lone_fail` in `why`: §6 says «decide ella», §5 defines the isolated peak on two.
- **T4 counts under one bar of the mother**, as §5 writes it; §0.1's 86 % is «under one hour»
  for an M30 mother, the sibling's bar.

## The build trades (phase 2)

`inputs.build_banks(batch folder)` is the only place that knows where they are: `{timeframe:
databank}` under `build_databanks` of the batch's `blocks.json`, else `CROSSTF_BUILD`'s name for each
sibling timeframe of its `blocks` (`afterrun` exports those databanks after step 11.7),
`{}` without a `blocks.json`. Each databank's
`trades.parquet` is read beside the `CrossTF` export; the mothers' own build trades come from the
gate's harvest of `Results`, by identity. No build → T1 and T2b are `no_build_data`, and `state`
is phase 1's capped at limbo.
