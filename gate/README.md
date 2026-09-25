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
| `harvest.py` | **The cosecha**: matches the build and retest databanks on identity, takes both, writes the joined tables | `python3 -m gate.harvest --project P --databank build --oos-databank oos1` | two databanks → four files + manifest |
| `pairing.py` | Matches the two databanks: on identity first, on file name for whatever identity missed | imported | two indexes → pairs, aliases, unpaired |
| `collect.py` | One side of it: stage a set of `.sqx` once and take its metrics, trades and equity | imported | files → three frames |
| `inputs.py` | The knobs, one harvest read back, and the two windows glued into one curve | imported | folder → frames, split, end |
| `screens.py` | The five cheap screens and the registry the cascade reads | imported | harvest + survivors → value, passed |
| `monkey.py` | The two screens that need the null study: the monkey, and the family correction over it | imported | trades + bars → p |
| `redundancy.py` | The soft screen: are these N strategies or one repeated N times | imported | equity → groups |
| `cascade.py` | Runs the screens in the config's order, each over what the last left, and writes the verdicts | imported | harvest → scorecard, funnel |
| `report.py` | **The gate over one harvest** | `python3 -m gate.report --project P --databank build --feed XAUUSD_DukasM1_Infinox` | harvest → `scorecard.parquet`, two `verdict.csv`, `resumen.md` |
| `config.yaml` | The screens as data: order, kind, thresholds, and why each exists | edited | — |

Manual page, in Spanish, for whoever runs it: `docs/manual/29-puerta.md`.
Design dossier: `docs/AgentPDFs/puerta-oos-2026-09-23.md`.

## The four things this module exists to get right

**The join is on identity, never on a name.** `core.sqxfile.identity` is the SHA-256 of the inner
`strategy_Portfolio.xml` **normalised** — a retest rewrites `makeExternal` on every `<variable>` and
nothing else, so the raw hash gives one identity in the build databank and another in the retest one
(🔬 0 of 115 matched raw, 115 of 115 normalised). And a name does not identify anything: two databanks
of this project hold *entirely different strategies* under the name `Strategy 17.8.29`. The scorecard
is indexed by identity and carries both databanks' names as labels — `strategy` from the retest,
`strategy_build` from the build.

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
  `(IS)` and `XAU_ISOOS_ejemplo/OOS` under `(OOS)` (`knowhow/04-export.md`). `collect.measured()`
  compares only the metrics the view emits at both types, because structural columns like
  `Param Count (IS)` carry a number whatever ran, and **refuses** when both blocks are filled: that
  databank ran its own split and no half of it can be called "the retest" from outside.
- **The equity curve is glued on daily returns, not on levels.** The two runs start from their own
  balances and their windows can overlap by a few bars of warm-up; the boundary is the first day the
  retest covers, and whatever the build window ran past it is dropped rather than double counted.
- **The monkey inherits the retest's costs for free.** `nulls.calibrate` measures what SQX charged
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

`gate` imports `core`, `nulls` and `tasks.analysis` (`decay` for the degradation maths,
`correlations.discoveries` for Benjamini-Hochberg). Nothing imports `gate` yet; `pipeline/` is where
it will, as the row that thins a population before the per-mother protocol starts. `tasks/analysis`
is a library folder with no entry points, so importing it does not point the arrow backwards — but a
screen that needs new maths **extends that module** rather than growing a second copy of Lo (2002).

## What this module deliberately does not do

- **It never applies its own verdict.** `sqx/curate/apply_verdict.py` does, with `--apply`, with the
  install stopped and with a record of what left.
- **It cannot undo selection.** If the build's acceptance conditions already read the out-of-sample
  period, the population was filtered by the very sample being judged and every screen reads as inert
  — measured on `XAUUSD/OOS`, where 229 of 231 are profitable out of sample, median Sharpe retention
  is 1.00 and the monkey kills nobody. On an unselected population the same screens leave 45 of 120,
  retention is 0.45 and 5 of 45 beat the monkey at 5 % (`knowhow/07-practices.md`). The gate records
  what it judged; it cannot un-select it.
- **It does not choose the statistic the monkey is read on.** `config.yaml` does, and that choice
  moves the verdict more than the null does.

## Where `gate.harvest` spends its time

🤔 Inferred from the code and the catalogue's timings, not yet broken down by phase (2026-09-25).
Per databank side, `collect.tables()` starts and stops the conductor once for the metrics export
(~21.5 s until the CLI answers, 14.7 s to stop) and launches one more `sqcli` for `orderstocsv`.
Two sides make two worker cycles and two JVM starts, which is most of the 112 s measured on
500 + 500 files. The Python part (packing, curves read from the `.sqx`) is seconds.

🔬 **Of the whole metrics export, the cascade reads one column**: `Net profit [OOS]`, in the
`estaticas` screen. Everything else it reads comes from the trades and the curves. The rest of
`metrics.parquet` is kept for the owner, not for a screen. `core.sqxstats.stats()` decodes the same
frozen `SQStats` from the `.sqx` with no JVM, so the metrics side can be replaced once its columns
are checked against a view export.
