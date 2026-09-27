# gate — two databanks in, one verdict per strategy out

The screening that happens after a build and its out-of-sample retest, and before anything
expensive. Thousands of strategies enter, a cascade of screens thins them, and what comes out is a
`verdict.csv` that `sqx/curate/apply_verdict.py` already knows how to apply.

**It reads two databanks, not one.** SQX charges one spread and one slippage per backtest, and these
windows are years long over an asset whose price moves a great deal, so the build and the retest are
two separate tasks with their own costs — and therefore two databanks. The harvest joins them.

```
config.yaml ─▶ harvest ─▶ cascade ─▶ scorecard ─▶ verdict ─▶ resumen
 the screens   two        each       every        what SQX   the funnel
 as data       databanks  screen     number per   can apply  and what
               matched    over what  strategy                each screen
               on         the last                           cost
               identity   left
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `harvest.py` | **The cosecha**: matches the build and retest databanks by strategy name, takes both, writes the joined tables | `python3 -m studies.screening.gate.harvest --project P --databank build --oos-databank oos1` | two databanks → four files + manifest |
| `pairing.py` | Matches the two databanks by strategy name (owner, 2026-09-26); identity stays the key downstream | imported | two indexes → pairs, aliases, unpaired |
| `collect.py` | One side of it: stage a set of `.sqx` once and take its metrics, trades and equity | imported | files → three frames |
| `inputs.py` | The knobs, one harvest read back, and the two windows glued into one curve | imported | folder → frames, split, end |
| `screens.py` | The five cheap screens and the registry the cascade reads | imported | harvest + survivors → value, passed |
| `monkey.py` | The two screens that need the null study: the monkey, and the family correction over it | imported | trades + bars → p |
| `redundancy.py` | The soft screen: are these N strategies or one repeated N times | imported | equity → groups |
| `cascade.py` | Runs the screens in the config's order, each over what the last left, and writes the verdicts | imported | harvest → scorecard, funnel |
| `one.py` | One strategy through the gate as the contract's data: MANTENER or DESCARTAR, and every screen with its number | imported — the window calls it | scorecard row → result |
| `many.py` | The cascade and the funnel as one result, and every strategy's own | imported | harvest → results |
| `report.py` | **The gate over one harvest** | `python3 -m studies.screening.gate.report --project P --databank build --feed XAUUSD_DukasM1_Infinox` | harvest → `scorecard.parquet`, `funnel.csv`, two `verdict.csv`, `gate.md`/`.html`/`.json`, one page per strategy |
| `tooltips.py` | One sentence per `config.yaml` knob, addressed by the screen's name, for the window's configuration drawer | imported | — |
| `config.yaml` | The screens as data: order, kind, and why each exists. Each threshold is a `ledger:<key>` placeholder: the number lives in `ledger/thresholds.yaml`, and `inputs.config()` fills it in before applying `--set` | edited | — |

Manual page, in Spanish, for whoever runs it: `docs/manual/05-cribado-oos.pdf` (cap. 29-puerta).
Design dossier: `docs/AgentPDFs/puerta-oos-2026-09-23.md`.

## The four things this module exists to get right

**The join is on the strategy name** (owner, 2026-09-26). The retest databank is a retest of the build
one inside the same project, and a strategy keeps its file name through it; within one databank a name
is unique, because SQX renames on collision. The scorecard stays indexed by identity —
`core.sqxfile.identity`, the SHA-256 of the inner `strategy_Portfolio.xml` normalised (a retest
rewrites `makeExternal` on every `<variable>`) — and a pair whose identity changed is re-keyed to the
build's. ⚠️ A name identifies nothing ACROSS projects or builds: two databanks of one project once held
entirely different strategies under `Strategy 17.8.29`. Pair only a retest with the build it retested.

**A strategy the retest databank does not hold is a reject, not a gap.** SQX drops a strategy when one
of its own red flags fires there — too many ambiguous trades, and the rest — and that decision stands
(owner, 2026-09-23). The `presencia` screen is first, it kills them, and because the match happens
*before* anything is staged, **nothing expensive is ever spent on them**: on `XAU_ISOOS_ejemplo`, 5 of
120 died at `presencia` and only the 115 pairs were ever exported.

**One cosecha, then nothing touches SQX again.** Each side is staged once and gives up its metrics,
its trades and its daily equity in that single pass. That is what makes adding an eighth screen cost
zero minutes of machine — and why the harvest is dated and immutable: a verdict is only reproducible
against the exact set it judged.

**The screens are data, not code.** `config.yaml` is the only place that says what the gate is. Each
row carries its own thresholds and its own `why`, and both are printed into the report, because a
funnel read without its thresholds says nothing. The gate stores **numbers, never judgements**:
changing a threshold re-judges without recomputing anything that costs machine time.

## What the two windows being two backtests changes

- **The metrics are joined side by side**, `<metric> [IS]` from the build databank and
  `<metric> [OOS]` from the retest one. **Which of the view's two blocks each side filled is read off
  the data, never assumed**: 🔬 a task that ran one window fills the block SQX designated it as, and
  two real retest databanks over the same window disagree — `XAUUSD/SPP OOS` puts its numbers under
  `(IS)` and `XAU_ISOOS_ejemplo/OOS` under `(OOS)` (`knowhow/export/databank-metrics-is-oos.md`). `collect.measured()`
  compares only the metrics the view emits at both sample types, because structural columns like
  `Param Count (IS)` carry a number whatever ran, and **refuses** when both blocks are filled: that
  databank ran its own split and no half of it can be called "the retest" from outside.
- **The equity curve is glued on daily returns, not on levels.** The two runs start from their own
  balances and their windows can overlap by a few bars of warm-up; the boundary is the first day the
  retest covers, and whatever the build window ran past it is dropped rather than double counted.
- **The monkey inherits the retest's costs for free.** `engines.market.calibrate` measures what SQX charged
  from the trades themselves, so the null runs are priced with the retest task's own spread and
  slippage without this module ever knowing what they were.

## Two verdicts, because a verdict names one databank

`verdict.csv` names the **retest** databank's strategies — the population that goes forward.
`verdict_build.csv` names the **build** databank's, and it is the only one that can carry the
strategies SQX dropped from the retest: they have no name in the retest databank at all.

## What is hard and what is soft

`kind: hard` eliminates; `kind: soft` measures everybody and eliminates nobody. Two screens are soft
on purpose:

- **`familia`** is a statement about the population — how many of the survivors chance alone would
  have handed over — and reading Benjamini-Hochberg as a per-strategy verdict is a decision the owner
  has not taken.
- **`redundancia`** groups by the strategy's own structure — the ordered block keys of its XML, with
  parameter values ignored — which replaced grouping by equity correlation (owner, 2026-09-23):
  correlation is a proxy and depends on the window, while the XML is what the strategy *is*. Two
  strategies on one shape at different settings are still two bets, so nobody is eliminated. What it
  buys is knowing that 45 survivors are **13 structures, one of them holding 24 of them**.

## Where the arrows point

`gate` imports `core`, `nulls` and `studies.screening.analysis` (`decay` for the degradation maths,
`correlations.discoveries` for Benjamini-Hochberg). Nothing imports `gate` yet; `pipeline/` is where
it will, as the row that thins a population before the per-mother protocol starts. `studies/screening/analysis`
is a library folder with no entry points, so importing it does not point the arrow backwards — but a
screen that needs new maths **extends that module** rather than growing a second copy of Lo (2002).

## What this module deliberately does not do

- **It never applies its own verdict.** `sqx/curate/apply_verdict.py` does, with `--apply`, with the
  install stopped and with a record of what left.
- **It cannot undo selection.** If the build's acceptance conditions already read the out-of-sample
  period, the population was filtered by the very sample being judged and every screen reads as inert
  — measured on `XAUUSD/OOS`, where 229 of 231 are profitable out of sample, median Sharpe retention
  is 1.00 and the monkey kills nobody. On an unselected population the same screens leave 45 of 120,
  retention is 0.45 and 5 of 45 beat the monkey at 5 % (`knowhow/research/post-selection-bias.md`). The gate records
  what it judged; it cannot un-select it.
- **It does not choose the statistic the monkey is read on.** `config.yaml` does, and that choice
  moves the verdict more than the null does.

## Where `studies.screening.gate.harvest` spends its time

🔬 2026-09-27: **the metrics no longer need SQX.** `collect.metrics()` reads each file's SQStats
through `core/sqxview.VIEW`, the owner's «Export Data View» column for column — checked on
`USDJPY_emaCross_H1` Results/OOS against the view's own export: every column equal within 6e-8
relative (float32), `R Expectancy` more precise (the view rounds it to two decimals). That removes
the conductor cycle the metrics export cost per harvest (~21.5 s until the CLI answered, 14.7 s to
stop). The one JVM left is `orderstocsv`, a one-shot `sqcli` for both sides at once. The Python part
(SQStats, packing, curves read from the `.sqx`) is seconds.

The cascade still reads one metrics column, `Net profit [OOS]`, in `estaticas`; the rest of
`metrics.parquet` is kept for the owner and the window's Ficha.
