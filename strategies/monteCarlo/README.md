# strategies/monteCarlo — how much of this result is luck, and of what kind?

One study, one folder. It runs **after** the strategy has already been accepted — it survived the
OOS decay test and the cross-market retest — and it does not ask whether the edge is real. It asks
what the edge depends on: the order the trades arrived in, which trades occurred at all, how they
were filled, and the regime they lived in.

Read `POSSIBLE_IMPROVEMENTS.md` before extending any of this, and `docs/manual/07-montecarlo.md`
before running it.

```
config.yaml ─▶ inputs ─▶ model ─▶ simulate ─▶ verdict ─▶ render
 every knob    the input  how a run    the        the        the
               contract   is made      numbers    vetoes,    report
                          different               the score
```

## The folders are the argument

The four boundaries of rule 5 of `CODESTYLE.md`, in the order the data flows, plus the layer that
writes it down. Each folder carries its own `README.md` saying what it holds, what it must never
hold, and the traps a future session would otherwise step in.

| folder | the question it answers | read its README before |
|---|---|---|
| `inputs/` | what is this study being run on? | touching the trade contract, the costs or a config key |
| `model/` | what are we pretending could have happened instead? | adding or changing a randomisation |
| `simulate/` | what are the numbers, under a given model? | touching the parallelism or a sweep |
| `verdict/` | given those numbers, what do we conclude? | moving a threshold or a score |
| `contract/` | how is all of that read? — the result as the contract's blocks, one tab per family | adding a figure, a table or a sentence |

The panel and the hand-drawn pages are gone (2026-09-25, `docs/encargos/19-…`): the window paints
`one.run()`'s dict with native widgets, and `core/study/render` draws the batch page from the same
dict, so the two cannot disagree.

| file | what it does | run it |
|---|---|---|
| `run.py` | Puts one stream through all five families and returns the raw result the verdict reads | imported |
| `load.py` | Everything one run reads, assembled once: the streams, the daily bars, the costs, each strategy's identity, and the stability check | imported |
| `one.py` | **One strategy as the contract's data**: verdict, seven tabs, warnings, glossary, summary row; `only=` re-runs one sub-test | imported — the window calls it |
| `many.py` | Every strategy, one process each, and the databank read as one result | imported |
| `report.py` | The command: every strategy of one databank, to `verdict.csv`, one JSON and one page per strategy, and the databank page | `python3 -m strategies.monteCarlo.report --project XAUUSD --databank Results --asset XAUUSD --export 2026-09-03` |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported |
| `config.yaml` | Every tunable of the study, grouped by family | edited, or `--set section.key=value` |

`run.py` is the one module allowed to cross every layer — that is what an orchestrator is. Everyone
else obeys one direction:

| layer | may import |
|---|---|
| `inputs/` | `core/` |
| `model/` | nothing inside the module |
| `simulate/` | `inputs/`, `model/`, `verdict/confidence` |
| `verdict/` | `inputs/`, itself |
| `contract/` | everything above it |
| `run.py`, `load.py`, `one.py`, `many.py`, `report.py` | everything |

`report.py` produces numbers and judges none of them; `verdict/gates.py` owns every threshold in the
study and computes none of the numbers it judges.

## What it does not do, by design

- **It does not measure overfitting.** No Deflated Sharpe, no CSCV, and there will be none here:
  both need the population of strategies tried during generation, which does not exist at this
  stage. Fabricating a trial count would produce a credible, false number. That question belongs to
  the generation study.
- **It does not validate the edge.** It assumes it and measures what it rests on.
- **It is not reproducible, on purpose.** No seed anywhere: every run draws fresh entropy.
  `simulate/stability.py` replaces reproducibility by measuring how far the gate-driving numbers
  move between independent runs — which is the question a seed hides.

## The input contract is the only contract

Every family takes a time-ordered trade list and nothing else. That is why a **portfolio** needs no
separate code: `inputs/stream.portfolio()` concatenates several strategies' trades, sorts by time,
and the same families run unchanged (`--portfolio`). `stream.overlap()` measures how often two
positions were open at once, and the report says so when they were: the additive equity curve is
still valid, but the longest losing run means something different at portfolio level.

## Costs come from the backtest, not from a guess

The trade export carries no cost column, so the cost of each trade is **recovered** as
`gross − net` (`core.trades.cost`), which is commission and swap exactly as SQX booked them. The
asset file supplies the spread and the point value, from its `sqx_default` side rather than its
`use:` side: this study stresses a backtest SQX already ran, so the costs that belong in it are the
ones that were charged in it. `inputs/costs.crosscheck()` compares the modelled commission against
the recovered one and warns when they diverge — the warning travels with the report and invalidates
Family C only, not the rest.

## Adding a way of randomising

Write a function in `model/draws.py` with the shared signature — `(n, size, rng, block)` in, an
index matrix out — add it to `DRAWS`, say what it preserves in `PRESERVES`, and put it in `FAMILY`.
A Family C perturbation is the same: a function in `model/stress.py`, a row in `MODELS`, and a floor
in `verdict/gates.py`. Nothing else changes.

The rule that keeps it honest is `KEEPS_MULTISET`: the two models that only reorder must leave net
profit identical to the last decimal. `simulate/sweeps.invariant()` measures it and every report
prints it. A non-zero there is a bug in the model, never a property of the strategy.
