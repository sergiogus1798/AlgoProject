# studies/transfer/crossTF — does the edge survive being looked at on a slower clock?

One study, one folder. A strategy built on H1 is rescaled to H4 (or M30 to M15), run on both, and asked
whether what it earns on H4 is its own or inherited from H1. Read
`docs/manual/07-otros-mercados-y-timeframes.pdf` (cap. 31-crosstf) before running it.

```
scaling.parquet ─┐
                 ├─▶ inputs ─▶ cells ─▶ verdict ─▶ report
trades.parquet ──┘   what the  what each  what it    the
                     cells     cell is    means      panel
                     are       worth
```

## The two questions, which are not the same question

| | what it asks | what a failure means |
|---|---|---|
| **scaled** — periods divided by the timeframe ratio | does the edge tolerate coarser resolution and a 0–4 h delay in acting? | evidence against the strategy |
| **unscaled** — the mother's periods left alone | is the market self-similar at this scale? | **nothing about the strategy** — it is graded nowhere and carries no verdict |

## One view, not two (2026-09-30 feedback §5)

The window shows scaled and unscaled together in one tab, `mother`/`statistic`/`scope`
selectors switching what is drawn — never what is computed: `cells.numbers` prices every
statistic of `engines.nulls.stats` on the same draws, so `statistic` is free (its «Sharpe total» replaces the per-trade Sharpe on the selector since 2026-10-01: `core.significance.annual_sharpe` of the cell's trades by close date, read but never judged — the null draws have no calendar), and `scope`
only toggles between the two tables (`Cada hermana escalada` vs `La madre sin escalar`). The
verdict itself never moves with a selector; it is read once, off `config.yaml`'s
`verdict.statistic`. Every cell — baseline, control, scaled and unscaled alike — is judged
against the **same null** (`verdict.rung`, `timing` by default: it shuffles only *when* each
trade enters, on that cell's own timeframe's bars); only the bars it is drawn on change.

## The new reading — «is the edge an isolated peak on its timeframe?» (encargo 47) — ⚠️ built BESIDE, NOT yet the live rule

Owner, 2026-10-07: the step-12 criteria are redesigned and written **next to** the old reading. The
**live rule is still `crossTF.combined.z_new`** (`criteria.yaml`, step 12) until a real run validates
the new one and the owner says «corta»; until then the new tests emit facts and judge nobody. Code
and tables: `tf/README.md`. The cut package (the two rules to paste, the list of what is deleted) is
at the end of `docs/encargos/47-paso-12-otras-temporalidades-pico-aislado.md`.

- **One null for the whole family.** A mother and all her siblings go through the *same* random
  runs: one whole-week shift per calendar year and run, never across the build / oos1 frontier,
  priced by the one repricer at the doctrine's size, in R (`tf.runs`: 5,000 draws, a fixed seed,
  written in the output). A calendar cell with a data hole in ANY timeframe is dropped in all of them.
- **Two windows.** oos1 (step 11) and `build` (step 11.7, the phase-2 twins `CrossTF <TF> build` →
  databank `CrossTF_<TF>_build`). The mother's build trades come from where they already exist.
- **Tests, per sibling then per mother.** `T0` comparable (not `unverified`/`clamped`, rounding
  shift ≤ 0.25, ≥ 30 trades in the window) · `T1` trade frequency `z_frec` (build + oos1; 1.5 passes,
  3.5 fails) · `T2a` oos1 retention `ret` and `z_delta` (0.5 · 1.65; isolated peak at 0.25) · `T2b`
  build `z_build` (1.65 · 0; isolated peak = both neighbours ≤ 0) · `T3` the far sibling failing T2a
  lowers a PASS to LIMBO · `T4` entry overlap and build retention, annotated only.
- **The cascade.** 11 SQX on oos1 → **11.5** this study, phase 1 (T0, T2a, T3 with what oos1 has;
  T1 and T2b read «no data») → **11.7** SQX on `build`, only the mothers still in `CrossTF_Input`
  (skipped, with a line, in a project without phase-2 tasks) → **12** the same study again, with the
  build. With no cut yet, 11.5 drops nobody, so every mother runs phase 2 — what the validation needs.
- **Neighbours.** M30 mother: M15 and H1, far H4. H1 mother: M30 and H4, no far one; D1 only annotated.
- **Outputs**, in the run's folder beside the old ones: `tf_siblings.parquet` (one row per mother ×
  timeframe: T0 and its reason, `z_frec`, `e`, `ret`, `z_delta`, `z_build`, window matches,
  `ret_build` and its percentile, a state per test) and `tf_mothers.csv` (one row per mother: states of
  T1/T2a/T2b/T3, `phase1`, `state`, seed, runs). States are `pass | limbo | fail`; the autopilot reads
  them as numbers (pass 1, limbo 0, fail −1) in facts `crossTF.tf.*` (`pipeline/autopilot/tffacts.py`).
- **Open owner decisions** (K-1 the R of `ret`, K-2 a lone neighbour that fails, K-3 T4's window):
  `tf/README.md` › Open readings. Not verified on real SQX data yet: `OPEN.md` #108.

## The reading of 2026-10-02 (still LIVE) — ⚠️ an agent's proposal, pending the owner

The owner decided that day that **the step reads oos1 only**; how the reading follows is this
proposal (`verdict.py`, `cells.beyond`, `tests/test_crosstf_facts.py`), not yet approved.

- **Only oos1.** `crosstf.segment` is `oos1`, so the SQX tasks retest only that segment, at its
  costs; `inputs.oos` cuts an older `build..oos1` export to the same. Every cell's statistic,
  null, p and `z` are oos1's. A mother was selected on `build`: her p there was 0.0004 by
  construction.
- **`z`** — the cell's statistic minus its null's mean, over the null's sd. Against a
  break-even strategy it is N(0, ~0.95): 1.65 and 2.33 are the 5 % and 1 % lines.
- **`z_new` — what a sibling adds beyond its mother.** A sibling re-reads the same asset over
  the same years. Under no edge its z follows its mother's with correlation ρ (0.5–0.95 for
  the ×2 timeframe, 0.3–0.7 for H4), so a sibling of a mother who cleared 1.65 by luck clears
  1.65 itself 14–40 % of the time, not 5 %. `z_new = (z − ρ·z_mother) / √(1 − ρ²)`, with ρ
  the pair's own monthly-P/L correlation (`corr_vs_baseline`, kept in [0, 0.95]), is a
  standard normal under no edge whatever the mother's luck: 3.7 % above 1.65 given a mother
  above 1.65, against 30 % for the raw z (smoke null, `AlgoData/scratch/calib_step12/`).
- **The mother's sum** — on her baseline cell: `combined_n_tested` (usable siblings with a
  `z_new`), `combined_z_new` (their sum over √n; what two siblings add is uncorrelated under
  the null, 0.03–0.07) and `combined_z_new_max`. Facts `crossTF.combined.*`: one key for any
  mother's timeframe, which is what a rule of `criteria.yaml` needs.
- **Six readings, in this order**: `unusable` (ONLY a custom-block length nobody could rule
  on, so the sibling could not be scaled — owner, 2026-10-02, «Redondea donde puedas, ya
  está»: rounding and the floor of 2 no longer discard a sibling; `rounding_shift` and
  `clamped` are recorded numbers and facts, to measure with, never a gate) · `silent` (no oos1 trade) · `no_data` (under 30
  oos1 trades on the sibling or on its mother — «sin datos», never `inherited`) · `survives`
  (p < alpha AND `z_new` over alpha's normal quantile) · `inherited` (made money in oos1, no
  more than its mother predicts) · `fails` (lost money in oos1). The first three mean the test
  did not happen: limbo for a rule, never a failure.
- **The control is shown, not read.** It is the sibling's parameters on the mother's bars; with
  periods ÷ 4 that is another strategy, not a rounding check. As a reading (`control_failed`,
  until 2026-10-02) it took 29 of 46 real siblings and inverted for a negative baseline.
- **A seed.** `--seed N` (or `run.seed`) replays the nulls exactly; the manifest records
  `nulls_seed` either way. A rule on a p or a z needs it fixed.

**D1.** The doctrine still lists D1 for an H1 mother (its own task, MetaTrader 4), but every D1
sibling of an H1 Simple Strategy is clamped (exits of 2–24 bars ÷ 24): the criteria calibration
of 2026-10-02 runs without it (owner: «quítalo») through `crosstfload --targets M30 H4`, which
leaves the doctrine and the D1 task's design alone. Every other target runs and is read for
every mother: M30 → H1 and H4, H1 → M30 and H4.

## What the fabrication scales (changed 2026-10-07, encargo 47 part F)

The owner's rule of 2026-09-23 was «periods and bar-count exits, nothing else», which left the H4
stop physically about twice as wide in price as the H1 one. It is superseded: the sibling also
carries every coefficient that multiplies a **per-bar** measure (`bar` in `sqx/variants/ranges.yaml`:
an ATR multiple, a candle-range multiple) divided by `c`, the measured ratio of the median ATR on
its timeframe over the mother's (build + oos1 of the asset). `window` (a Bollinger deviation over N
bars, already scaled) and `other` (thresholds without price units) do not move; a coefficient on an
unclassified measure marks the sibling `unverified` (T0 reads it). At step 10.5 strategies carry no
stop or target (`assets/_build.yaml` `stop_loss`/`profit_target` false; the stop is grafted at step
24), so today only condition-block coefficients move. The old declared property below applies to the
2026-10-02 reading's runs made before the change. `knowhow/sqx-drive/crosstf-scaling-coefficients.md`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `inputs.py` | The knobs, which timeframe each block is (a sibling's cells also carry what the fabrication did to it: `ratio`, `n_scaled`, `rounding_shift`, `clamped`, `unverified`), and `oos`: the cut to oos1 and which databank holds it (`blocks.json` first, today's doctrine only as a fallback for a run without one; `gather` reads one export per timeframe), and the bars of each timeframe | imported | config + manifests → cells, bars |
| `cells.py` | What each cell earned in oos1 and where it sits among its own timeframe's nulls: the statistic, its p, the null's mean and sd, `z`; `corr_vs_baseline`; and `beyond`: each sibling's `z_new` and the mother's `combined_*` | imported | trades + bars → statistic, p, z |
| `verdict.py` | What a scaled cell means on oos1, beyond what its mother explains (the proposal above) | imported | panel → one of six readings |
| `many.py` | What the study reads, every cell measured and every scaled cell read, as one result the window paints | imported | export + scaling → result |
| `equity.py` | The two equity charts per mother (unscaled, scaled; Net Profit in every legend entry) and `per_mother`, the one mechanism that tags a block `select: mother` so the window's «Madre» picks it. Grids and the outcome bars are about all mothers and say so in their title | imported | plan + trades → blocks |
| `report.py` | **The command**: prints the result and writes it to `reports/<P>/<D>/<export day>/crossTF/` — the page, `verdict.csv` (one row per scaled sibling, its reading as `verdict`) and `cells.parquet`. `--strategy MOTHER` reads that one mother alone (feedback 2026-09-30 §5: "Run solo esta estrategia" is a real, cheaper run, not just a hidden button) and writes only `estrategias/<mother>.json` — never `verdict.csv`, `cells.parquet` or the population page, which until 2026-10-01 it overwrote with that one mother and the databank tab lost the other 14 (same rule as crossmarket's `--strategy`) | `python3 -m studies.transfer.crossTF.report --project P --asset USDJPY [--databank CrossTF] [--day DAY] [--fabricated DAY] [--strategy MOTHER] [--seed N]` | export → reports |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported | — |
| `config.yaml` | Every tunable, grouped by section | edited, or `--set section.key=value` | — |

Dependencies point one way: `inputs` → `core`; `cells` → `core`, `nulls`; `verdict` →
nothing inside the module; `report` orchestrates.

## The trap a future session will step in

**Each timeframe is its own SQX task and its own databank** (owner, 2026-09-30): `CrossTF` runs the
mothers' timeframe (block 0), and `CrossTF_M30`, `CrossTF_H4`, `CrossTF_D1` (D1 on the MetaTrader 4
engine) the others. They used to be blocks of one `RetestOnAdditionalMarkets` task, and that export
cannot be split on one symbol: the rows come sorted by open time and the k-th occurrence of a
ticket labelled the blocks by how fast each traded — from H1, M30's trades were scored as the H1
baseline (`knowhow/export/data-all-blocks.md`). `inputs.blocks()` reads the timeframes and
`inputs.gather()` the databanks from `blocks.json` beside `scaling.parquet`, both written by
`sqx.projects.crosstf` for THIS run; each databank's export is found beside CrossTF's, the same day
first. A run without `databanks` in its `blocks.json` is an old cross-check run: its packed `block`
column is kept, and it is not trustworthy. Only such a run falls back to today's
`crosstf.timeframes` (OPEN.md #80). `report.py` prints the mapping before any number.
