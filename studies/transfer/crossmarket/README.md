# studies/transfer/crossmarket — does the edge transfer to markets it never saw?

One study, one folder. It asks whether a strategy's entry timing carried information on markets it
was never optimised on, or whether it was only being long while those markets rose. Read
`POSSIBLE_IMPROVEMENTS.md` before extending any of this, and `docs/manual/05-retest-mercados.md`
before running it.

```
config.yaml ─▶ inputs ─▶ mechanics ─▶ engines/nulls ─▶ simulate ─▶ verdict ─▶ contract
 every knob    what the   what a        what could   the         what there   the
               study      trade         have         numbers     is to        tabs
               runs on    occupied      happened     under a     distrust
                          and was       instead      model       about them
                          worth
```

## The folders are the argument

The four boundaries of rule 5 of `CODESTYLE.md`, in the order the data flows, plus the bar-level layer
this study needs and `monteCarlo/` does not, plus the layer that writes it all down. Each folder
carries its own `README.md` saying what it holds, what it must never hold, and the traps a future
session would otherwise step in.

| folder | the question it answers | read its README before |
|---|---|---|
| `inputs/` | what is this study being run on? | touching a knob, a market declaration or a cost |
| `mechanics/` | what did a trade occupy, and what was it worth? | touching the pricing, the bar grid or the window |
| `simulate/` | what are the numbers, under a given model? | touching a test, the sweep or the portfolio |
| `verdict/` | what is there to distrust about them? | moving a threshold or adding a warning |
| `orchestrate/` | how does one strategy go through every market? | changing what a market's analysis runs |
| `contract/` | how is all of that read? — the twelve tabs as the contract's blocks | adding a figure, a table or a sentence |

Only these sit in the root, because they are the only things that get called or edited:

| file | what it does | run it |
|---|---|---|
| `load.py` | Everything a run reads, once: the export, its market universe, every feed's bars, the strategy names and their identity | imported |
| `one.py` | **One strategy across every market, as the contract's data** — twelve tabs, the breadth verdict, warnings, glossary; `only=` runs one market alone | imported — the window calls it |
| `many.py` | Every strategy judged on breadth, one (strategy, market) task per process: the verdict `/curate` applies | imported |
| `report.py` | The command: the batch to `verdict.csv` and the export's page, or `--strategy NAME` for one strategy's whole study | `python3 -m studies.transfer.crossmarket.report --project P --databank D --asset USDJPY --export DAY [--strategy S]` |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported |
| `config.yaml` | Every tunable of the study, grouped by section | edited, or `--set section.key=value` |
| `assets/_markets.yaml` | What each base asset's markets are called, how they are grouped, and where its backtest's out-of-sample stretch starts | edited |
| `execution.yaml` | Per feed, what a worse broker would charge | edited |

`orchestrate/` is the one folder allowed to cross layers — that is what an orchestrator is. Everyone
else obeys one direction:

| layer | may import |
|---|---|
| `inputs/` | `core/` |
| `mechanics/` | `core/`, itself |
| `simulate/` | `inputs/`, `mechanics/`, `engines/`, itself, **`verdict/fieller`** |
| `verdict/` | `engines/`, itself |
| `contract/` | everything above it |
| `orchestrate/`, `load.py`, `one.py`, `many.py`, `report.py` | everything |

And it is checkable without running anything — each of these prints nothing but the one declared
exception, `simulate/exposure.py → verdict/fieller`:

```bash
cd studies/transfer/crossmarket
grep -rn "from studies.transfer.crossmarket" inputs/
grep -rn "from studies.transfer.crossmarket" mechanics/ | grep -v "crossmarket\.mechanics"
grep -rn "from studies.transfer.crossmarket" verdict/  | grep -vE "crossmarket\.(model|verdict)"
grep -rn "from studies.transfer.crossmarket" simulate/ | grep -vE "crossmarket\.(inputs|mechanics|model|simulate)"
grep -rn "from studies.transfer.crossmarket" contract/ | grep -vE "crossmarket\.(inputs|mechanics|model|simulate|verdict|contract)"
```

`simulate/` produces numbers and judges none of them; `verdict/` names every reason to distrust a
number and computes none of the numbers it names.

## The three questions a reader asks first

**Where is a threshold changed?** In `config.yaml`, and nowhere else. `inputs/config.py` is the only
module that reads that file; `verdict/` is the only layer that turns a key into a consequence, and
`tooltips.py` holds the one sentence the config drawer shows for each knob. Nothing in
`simulate/` or `contract/` holds a limit. → `inputs/README.md`, `verdict/README.md`.

**What do I touch to add a placement model?** Three things: the function in `engines/nulls/placement/trade_models.py`
(or `free_models.py` beside it if it re-lays the whole run) with the signature
`(held, market, draws, rng, batch)` → `(entries, holds)`; a row in `MODELS` **and** in `RANDOMISES`
saying what it randomises; and its key in `config.yaml` under `nulls.models`. The reader's Spanish
name goes in `contract/words.NAMES`. Nothing else changes. → `engines/nulls/placement/README.md`.

**Why can the panel not give different numbers from the report?** Because there is no report. The
panel is the only entry point, nothing is written to disk and nothing is cached: every number comes
from the run the owner just started, and `explorer/work.clear()` wipes any result an older version
left in `derived/crossmarket/` at start-up. The batch report was removed on 2026-09-15 at the owner's
request, because a stored result can always be read as an answer to a question it was not computed
for. → `explorer/README.md`.

## What this study does not do, by design

- **It issues no verdict, and it never drops a market.** Every market the export carried is reported
  in full, with the reasons to distrust its numbers named beside it. Which strategy to keep is the
  owner's call, made outside here. That is a change from the first build, which gated markets out of
  a vote and cost a Brent result at p = 0.005 because 8% of its entries were pending fills.
- **It does not measure overfitting.** No Deflated Sharpe: it needs the count of trials made during
  generation, which does not exist at this stage. That question belongs to the generation study.
- **It is not reproducible by accident.** `nulls.seed` fixes the draws, but a null model's randomness
  is keyed by the calendar where it has to match across markets — see `simulate/joint.py` — so
  sharing a seed is not what couples two markets.

## Rules these enforce, because each one has a direction

- **A market is never dropped.** It is reported with its warnings. Losing 100% of a market's evidence
  over 8% of its trades was the first build's worst habit.
- **The base asset never counts as evidence.** It is reported as the reference case: on the market it
  was optimised on, a strategy beats its null and its paired benchmark by construction. That says the
  code works, and nothing about the strategy.
- **Its out-of-sample stretch is the one exception, and it is reported apart.** The same random-entry
  test runs on the main backtest restricted to `assets/_markets.yaml`'s declared `out_of_sample` range — the
  project's own `<OutOfSample>` — because the builder optimised nothing there. It is kept out of the
  joint null, the breadth count, the portfolio and the correlation matrix: it is the same market, not
  a second one. → `explorer/README.md`, and read the `selected_window` warning before reading its p.
- **E is never a bare number.** It divides by the market's own drift, so where that drift is not
  distinguishable from zero the ratio has no finite interval at all. It is always shown with a
  **Fieller interval**, which returns the unbounded one and says so, beside the share of bootstrap
  replicates whose denominator changed sign. The number the panel leads with is **A per unit of
  risk**, which is defined everywhere.
- **A confidence interval brackets the estimator it is an interval for.** A's bootstrap is weighted by
  holds because A itself is pooled over occupied bars; unweighted, it sat 9% away from its own point
  estimate.
- **Long only.** `mechanics/pricing.require_long_only()` refuses anything else rather than silently
  flipping a sign. Checked: all 92,329 trades of the 30-strategy sample are Buy.
- **Every random run is priced in dollars**, with the real trades' own sizes and costs — which is what
  lets the study report net profit, drawdown, Ret/DD, Sharpe and PF rather than one abstract
  statistic. Measured, the P&L reconstructed from the bars correlates **0.9996** with the P/L SQX
  itself reported.
- **Read the luck figure before any p-value.** It is a scale for reading a table, not a rule.
