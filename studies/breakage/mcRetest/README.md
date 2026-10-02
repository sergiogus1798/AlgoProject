# studies/breakage/mcRetest — if the world had been slightly different, would these trades have happened?

> **"Retest" is overloaded in this repo.** `sqx/export/export_retest.py` means the *cross-market*
> retest, which is `studies/transfer/crossmarket/`. This folder is **Monte Carlo Retest**: SQX re-running
> the whole backtest a thousand times against a perturbed input.

One study, one folder. Every other robustness test in this project resamples a trade list that
already exists — `monteCarlo/` reorders it, `crossmarket/` re-places it on another market. The
strategy is never re-run. **This one is the opposite:** each simulation perturbs an input and runs
the entire backtest again against it. That is why it is slow, and why it answers a deeper question.
Not *"given this trade history, was the shape of the equity curve luck?"* but *"would this history
have existed at all?"*

It runs **after** the strategy has been accepted, and it does not ask whether the edge is real. It
asks **which single thing breaks it**: the cost of entering, the fill received, its own parameters,
the exact history it happened to see — or nothing at all.

Read `POSSIBLE_IMPROVEMENTS.md` before extending any of this, and `docs/manual/08-montecarlo.pdf` (cap. 11-retest-mc)
before running it.

```
config.yaml ─▶ inputs ─▶ model ─▶ measure ─▶ verdict ─▶ contract
 every knob    which runs  what a      the         the vetoes,  the
               and what    number      numbers     the score    report
               SQX did     means
```

## The folders are the argument

The four boundaries of rule 5 of `CODESTYLE.md`, in the order the data flows, plus the layer that
writes it down. Each folder carries its own `README.md` saying what it holds, what it must never
hold, and the traps a future session would otherwise step in.

| folder | the question it answers | read its README before |
|---|---|---|
| `inputs/` | what is this study being run on, and what did SQX actually do? | touching a task, a databank name or a config key |
| `model/` | what does a number read off a simulation mean? | touching a reconstructed formula or a confidence level |
| `measure/` | what are the numbers, and do they reconcile? | touching the ingest or the reconciliation |
| `verdict/` | given those numbers, what do we conclude? | moving a threshold or a score |
| `contract/` | how is all of that read? — the result as the contract's five tabs, every sentence in Spanish | adding a figure, a table or a sentence |

`measure/` is where a sibling study would say `simulate/`. Nothing is simulated here in Python —
SQX did that — and a folder named for something it does not do is exactly the trap these READMEs
exist to prevent.

Only the entry points sit in the root, because they are the only things that get called:

| file | what it does | run it |
|---|---|---|
| `ingest.py` | Reads the eight task databanks once, reconciles every reconstructed metric against SQX, and writes one dated immutable export | `python3 -m studies.breakage.mcRetest.ingest --project XAUUSD` |
| `run.py` | Puts one strategy through the four questions and returns the raw result the verdict reads | imported |
| `load.py` | Everything one report reads from one ingest, once: simulations, originals, the confidence table, provenance and identity | imported |
| `one.py` | **One strategy as the contract's data**: verdict, five tabs, glossary, summary row | imported — the window calls it |
| `many.py` | Every strategy, and what can only be said across them, as one result | imported |
| `report.py` | The command: every strategy of one ingest, to `verdict.csv`, one JSON and one page per strategy, and the ingest's page. `--strategy` («1.26.46» or «Strategy 1.26.46») runs `one.run` on that strategy alone and rewrites only its `estrategias/` JSON and page — `verdict.csv`, `mcRetest.json` and the battery's cross-strategy facts are the population's | `python3 -m studies.breakage.mcRetest.report --project XAUUSD [--strategy "Strategy 1.26.46"]` |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported |
| `config.yaml` | Every tunable of the study, grouped by the layer that reads it | edited, or `--set section.key=value` |

The browser panel is gone (2026-09-25, `core/study/CONTRACT.md`); the window paints `one.run()`'s dict,
and the batch page is drawn from the same dict by `core/study/render`. Reports land in
`reports/<P>/<D>/<day>/mcRetest/`, not `retest/`: "retest" alone also names the cross-market one.

## The four questions

Inference is organised by the questions a risk committee asks in order, not by test name. A test
earns its place by the question it answers, and each one lives in `verdict/`:

| # | question | file | what it settles |
|---|---|---|---|
| 1 | how much does it hurt? | `fragility.py` | tail quantiles with their uncertainty, and the conditional drawdown the account must survive |
| 2 | how does it hurt — gradual decay, or collapse? | `modes.py` | whether the outcome is one regime or two, and whether the trade count survived |
| 3 | what breaks it? | `attribution.py` | effect sizes between tasks, in units of the control |
| 4 | do I believe it? | `evidence.py` | whether an edge remains once shape and multiplicity are paid for |

## Traps that cost real time here

- **A confidence level is not a scenario.** Level 95 of `NetProfit` and level 95 of `Drawdown` come
  from two *different* simulations: each metric is ranked on its own. Read as a pair they describe a
  run that never existed. The parquet stores the level table **long**, so `df[["NetProfit",
  "Drawdown"]]` — which looks like a scenario and is not one — cannot be written by accident.
  Assembling a *coherent* worst case, the whole metric row of the one simulation that really was
  that bad, is not built yet; see `POSSIBLE_IMPROVEMENTS.md`.
- **`StandardDev` is `ddof=0`.** SQX's is the population deviation, measured against its own stored
  tables. `core/significance.py` deliberately uses `ddof=1` for a different job. Do not harmonise.
- **Only 30 of the 148 metrics are reconstructible per simulation.** The rest need dates or prices
  that a simulation file does not carry. `SharpeRatio`, `SortinoRatio`, `UlcerIndex`, `RSquared` and
  `Stability` are computed by SQX on the *daily equity curve* and are among them — any per-trade
  version is a declared analogue under a different name, never a replication.
- **The `bar` task is the denominator, not a test.** See `inputs/README.md`.
- **Three of the 40 runs have an unusable stored confidence table.** See `inputs/README.md`.

## What it does not do, by design

- **No Deflated Sharpe.** Same reason `monteCarlo/` and `crossmarket/` refuse it: DSR needs the
  population of strategies tried during generation, which does not exist at this stage. And a
  thousand retests of *one* strategy are not a thousand selection trials — feeding them in as `N`
  would produce a credible, false number. That question belongs to the generation study.
- **No p-value where the sample size is a knob.** With 1,000 simulations per task, Kolmogorov-Smirnov
  and Brown-Forsythe reject on every pair — measured, 30 of 30, from `6e-34` down to `0`. The
  statistic scales with `√n` and `n` is how long you let SQX run, so the exponent is a setting, not
  evidence. Effect sizes lead; those p-values are reported behind them and stay out of the
  multiplicity pool.
