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

## Why there is a control cell

A scaled sibling is run on **its own source timeframe too**, and that cell is the control.
Without it, "it died on H4" and "it died when its periods changed from 9 to 2" are the same
observation, and the study cannot tell which it saw. `verdict.MEANS["control_failed"]` is
that separation made explicit.

## What this study deliberately does not correct for

The scaling rule is the owner's, 2026-09-23: **periods and bar-count exits, nothing else**
(`sqx/variants/config.yaml`, section `crosstf`). So a `StopLossCoef` of 2 is written through
unchanged, and because the range it multiplies grows when bars are aggregated, **the H4 stop
is physically about twice as wide in price as the H1 one.** That is a declared property of
the comparison, not a bug — but it means an H4 cell is never a clean "same strategy, slower
clock", and nothing downstream should describe it as one.

| file | what it does | run it | in → out |
|---|---|---|---|
| `inputs.py` | The knobs, which timeframe each block is and which databank holds it (`blocks.json` first, today's doctrine only as a fallback for a run without one; `gather` reads one export per timeframe), and the bars of each timeframe | imported | config + manifests → cells, bars |
| `cells.py` | What each cell earned and where it sits among its own timeframe's nulls | imported | trades + bars → statistic, p |
| `verdict.py` | What a scaled cell means, once the control and the rounding have had their say | imported | panel → one of five readings |
| `many.py` | What the study reads, every cell measured and every scaled cell read, as one result the window paints | imported | export + scaling → result |
| `report.py` | **The command**: prints the result and writes it to `reports/<P>/<D>/<export day>/crossTF/` — the page, `verdict.csv` (one row per scaled sibling, its reading as `verdict`) and `cells.parquet`. `--strategy MOTHER` reads that one mother alone (feedback 2026-09-30 §5: "Run solo esta estrategia" is a real, cheaper run, not just a hidden button) and writes only `estrategias/<mother>.json` — never `verdict.csv`, `cells.parquet` or the population page, which until 2026-10-01 it overwrote with that one mother and the databank tab lost the other 14 (same rule as crossmarket's `--strategy`) | `python3 -m studies.transfer.crossTF.report --project P --asset USDJPY [--databank CrossTF] [--day DAY] [--fabricated DAY] [--strategy MOTHER]` | export → reports |
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
