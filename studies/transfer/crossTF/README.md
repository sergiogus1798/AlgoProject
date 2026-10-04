# studies/transfer/crossTF — does the edge survive being looked at on a slower clock?

One study, one folder. A strategy built on H1 is rescaled to H4, run on both, and asked
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

## The reading — ⚠️ an agent's proposal of 2026-10-02, pending the owner

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

## What this study deliberately does not correct for

The scaling rule is the owner's, 2026-09-23: **periods and bar-count exits, nothing else**
(`sqx/variants/lengths.py`: what SQX types a period, plus the custom-block table). So a `StopLossCoef` of 2 is written through
unchanged, and because the range it multiplies grows when bars are aggregated, **the H4 stop
is physically about twice as wide in price as the H1 one.** That is a declared property of
the comparison, not a bug — but it means an H4 cell is never a clean "same strategy, slower
clock", and nothing downstream should describe it as one.

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
