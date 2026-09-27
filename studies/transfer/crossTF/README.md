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
| `inputs.py` | The knobs, which cell each result block is, and the bars of each timeframe | imported | config + manifests → cells, bars |
| `cells.py` | What each cell earned and where it sits among its own timeframe's nulls | imported | trades + bars → statistic, p |
| `verdict.py` | What a scaled cell means, once the control and the rounding have had their say | imported | panel → one of five readings |
| `many.py` | What the study reads, every cell measured and every scaled cell read, as one result the window paints | imported | export + scaling → result |
| `report.py` | **The command**: prints the result and writes it to `reports/<P>/<D>/<export day>/crossTF/` — the page, `verdict.csv` (one row per scaled sibling, its reading as `verdict`) and `cells.parquet` | `python3 -m studies.transfer.crossTF.report --project P --asset USDJPY [--databank CrossTF] [--day DAY] [--fabricated DAY]` | export → reports |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported | — |
| `config.yaml` | Every tunable, grouped by section | edited, or `--set section.key=value` | — |

Dependencies point one way: `inputs` → `core`; `cells` → `core`, `nulls`; `verdict` →
nothing inside the module; `report` orchestrates.

## The trap a future session will step in

Which result block is which timeframe has to match the `<Setup>` order of the retest task.
`inputs.blocks()` derives it the way `sqx.projects.crosstf` writes it — the siblings'
`source_tf`, then `crosstf.timeframes` of `assets/_build.yaml`; `run.blocks` in `config.yaml`
is a list only for a task written with `--timeframes`. Get it wrong and every cell is priced on
the wrong bars, with no error anywhere. `report.py` prints the mapping before any number for
exactly that reason. The blocks are separated by the ticket restarting at 1
(`core.tradestore.block`) and **not** by the `Symbol` column, which is identical across the
timeframes of one asset.
