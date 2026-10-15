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
| `cascade.py` | Run the gate's levels in order, the step-8 rules of each right after it, each over what the last left. | imported | harvest → scorecard, funnel |
| `collect.py` | One databank's three tables, taken in a single staging of its files. | imported | files → three frames |
| `harvest.py` | Two databanks in, one joined cosecha out: the build window and the retest window. | `python3 -m studies.screening.gate.harvest --project P --databank build --oos-databank oos1` (`--exports`: also each databank's own trade export under `raw/`, from the same `orderstocsv`) | two databanks → four files + manifest |
| `inputs.py` | The knobs, one harvest read back, and the out-of-sample window read from the trades. | imported | folder → frames, split, end |
| `level0.py` | Level 0 of the gate: in the retest, readable and not a clone, net of oos1, trades per year of the build. | imported | harvest + alive → facts |
| `level1a.py` | Level 1a of the gate: R3, the t of the per-trade excess over the market's drift. | imported | harvest + bars + costs + alive → fact + per-trade table |
| `level1b_centred.py` | Level 1b of the gate, the facts centred on the population: frequency stability and decay inside oos1. | imported | oos trades + build trades + alive → facts |
| `level1b_data.py` | Level 1b of the gate: what the edge keeps without the trades that touch a feed anomaly. | imported | oos trades + anomaly inventory → facts |
| `level1b_onepass.py` | Level 1b of the gate, one pass over the trades: edge against cost, concentration and MAE. | imported | oos trades + alive → facts |
| `level2.py` | Level 2 of the gate: what the edge keeps when entry, exit or both slip one bar. | imported | per-trade table + bars + costs + alive → 2 facts + per-variant table |
| `level3ab.py` | Level 3a and 3b of the gate: homogeneity of the excess across quarters, and the drawdown against its resampled own. | imported | `data["oos"]`, `data["build"]`, `market["risk"]` + alive → facts |
| `level3c.py` | Level 3c of the gate: the strategy against monkeys drawn inside R3's drift window. | imported | oos trades + bars → facts |
| `levels.py` | The gate's levels in the order they run, and which level produces each fact. | imported | — → `LEVELS`, fact → level |
| `many.py` | The gate over one harvest: every level in order, and the population read as one result. | imported | harvest → results |
| `measures.py` | The scorecard's measured columns: numbers every paired strategy gets and no screen judges. | imported | trades + equity + bars → 14 columns |
| `one.py` | One strategy through the gate, as the contract's data: where it fell, and every fact of every level. | imported — the window calls it | scorecard row → result |
| `pairing.py` | Pair two databanks by strategy identity: the build's file and the retest's file of the same strategy. | imported | two indexes → pairs, aliases, unpaired |
| `redundancy.py` | The soft screen: are these N strategies, or one strategy repeated N times? | imported | equity → groups |
| `report.py` | The gate over one databank: the levels, the scorecard, and the verdict SQX can apply. | `python3 -m studies.screening.gate.report --project P --databank build --feed XAUUSD_M1 [--seed 20261002]` | harvest → `scorecard.parquet`, `funnel.csv`, two `verdict.csv`, `gate.md`/`.html`/`.json`, one page per strategy |
| `tooltips.py` | One sentence per config.yaml knob, for the window's configuration drawer. | imported | — |
| `config.yaml` | The screens as data: order, kind, and why each exists. Each threshold is a `ledger:<key>` placeholder: the number lives in `ledger/thresholds.yaml`, and `inputs.config()` fills it in before applying `--set` | edited | — |

Manual page, in Spanish, for whoever runs it: `docs/manual/05-cribado-oos.pdf` (cap. 29-puerta).
Design dossier: `docs/AgentPDFs/puerta-oos-2026-09-23.md`.

## The four things this module exists to get right

**The join is on identity, found by the strategy name** (owner, 2026-09-26). The retest databank is
a retest of the build one inside the same project, and a strategy keeps its file name through it;
within one databank a name is unique, because SQX renames on collision, so the name is what pairs a
build file with its retest file. Everything from there on — the scorecard, the screens, `verdict.csv`
— is indexed by identity, never by name: `core.sqxfile.identity`, the SHA-256 of the inner
`strategy_Portfolio.xml` normalised (a retest rewrites `makeExternal` on every `<variable>`) — and a
pair whose identity changed is re-keyed to the build's. ⚠️ A name identifies nothing ACROSS projects
or builds: two databanks of one project once held entirely different strategies under
`Strategy 17.8.29`. Pair only a retest with the build it retested, which is exactly why the name is
used only to find the correspondence and identity is what the join carries forward.

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

The monkey screen places its random entries on the harvest's own build timeframe (`inputs.timeframe`;
a mixed harvest refuses); `--set monkey.timeframe=` wins over it.

## What is hard and what is soft

`kind: hard` eliminates; `kind: soft` measures everybody and eliminates nobody. Two screens are soft
on purpose:

- **`familia`** is a statement about the population — how many of everyone the `mono` screen tested chance alone would
  have handed over (BH runs over that whole family, not over the survivors of the p screen) — and reading Benjamini-Hochberg as a per-strategy verdict is a decision the owner
  has not taken.
- **`redundancia`** groups by the strategy's own structure — the ordered block keys of its XML, with
  parameter values ignored — which replaced grouping by equity correlation (owner, 2026-09-23):
  correlation is a proxy and depends on the window, while the XML is what the strategy *is*. Two
  strategies on one shape at different settings are still two bets, so nobody is eliminated. What it
  buys is knowing that 45 survivors are **13 structures, one of them holding 24 of them**.

## Where the arrows point

`gate` imports `core`, `nulls` and `studies.screening.analysis` (`decay` for the degradation maths,
`tradelevel` and `floating` for the measured columns). Nothing imports `gate` yet; `pipeline/` is where
it will, as the row that thins a population before the per-mother protocol starts. `studies/screening/analysis`
is a library folder with no entry points, so importing it does not point the arrow backwards — but a
screen that needs new maths **extends that module** rather than growing a second copy of Lo (2002).

## The z — the one statistical rule of step 8 (owner, 2026-10-12, encargo 65 §5.2)

`z_mono` (the strategy's mean P/L per trade against the hours monkey, in the monkey's own sd) must
reach **Φ⁻¹(1 − 0.01/B)**, B = the batches screened on oos1 in the project's cell (asset × timeframe ×
direction × family) counting the current one (`ledger.cells.batches_for`): 2.326 with B = 1, 2.576
with 2, 2.807 with 4 (alpha 0.01 since 2026-10-15; it was 0.05). `criteria.yaml` declares only `alpha: 0.01, per: cell`; the line is computed by
`judge.per_cell` (the gate's `report.py` and the judge both call it, so they cannot disagree) and the
ledger row of the judgement records B and the line used (`thresholds`). No data means Fail. It replaces
R3, R5c's t and the old fixed `z_mono >= 1.65` as judges. **R4a, R5, R5b, R8 and R9b are columns**: still
computed and stored in the scorecard, judging nothing. The medoid cut (`medoids: 4`) runs after it.

**`p_fdr` — a column, not a rule** (owner, 2026-10-12; its cut waits for row 9 of encargo 65). `many.run` fits
`engines.inference.localfdr` on the `z_mono` of every strategy that reached level 3c in the lot — not on
`falsePositives`: an empirical null N(δ₀, σ₀²) from the central 50 % of z, π₀ (≤ 1), and
`p_fdr = 1 − π₀·f₀(z)/f(z)`, the probability the strategy is not null, 0 at or left of δ₀; fdr is made monotone by a cumulative maximum from the right (a z is as null as the worst fdr at or above it), so a lot whose tail is lighter than its own null gives p = 0 to everyone. With fewer than 500
z it is empty. The scorecard comes ordered: survivors first, by `p_fdr` descending, ties and empties by `z_mono`.
δ₀, σ₀, π₀ and the z read go in the population's funnel note and the manifest `counts`.

`monkey.draws` is **100,000** (it was 5,000; owner: no compute limits). The Monte Carlo standard error
of a z near the line is √((1 + z²/2)/n) ≈ 0.0048 at n = 100,000 (0.021 at 5,000), so the draw no longer
moves a verdict at 2.326 / 2.576 / 2.807 except for a strategy within about 0.01 of the line.
Measured 2026-10-12 on the USATEC export (`Test_USATEC_H1_ruptura_leaseWeb`, 169 alive, all cores):
**149 s** for level 3c, four rungs each, i.e. 0.9 s per strategy — so a gate that no longer cuts at R3
sends many more strategies to 3c: budget ~1 s per strategy per run, and the raw draws kept in
`distribuciones.parquet` grow with it (~0.4 MB per rung per strategy at float32).

## Measured, not judged (2026-10-02)

`measures.py` adds fourteen columns to the scorecard after the cascade, for **every** strategy the
retest databank holds — a strategy dead at `estaticas` has them too, so a `criteria.yaml` rule on
them never meets a fact the cascade did not compute. Nothing here eliminates; they become
`gate.scorecard.<column>` facts of the autopilot.

| column | what it is |
|---|---|
| `trade_t` | plain t of the mean OOS trade: mean / sd × √n of `Profit/Loss` |
| `drift_excess_t` | the same on each OOS trade's P&L **minus the market's drift over its hold** (side × mean bar-to-bar close change of oos1 × bars held × size × point value), at the AR(1) effective n. One line for longs and shorts, any asset, any window length. Equal to the calibration toolkit's `t_ex_ar1_oos` to 4e-16 on 5,048 strategies |
| `oos_trades_per_year`, `is_trades_per_year` | trades over the length of the asset's oos1 / build segment |
| `oos_max_dd_r`, `is_max_dd_r` | largest fall of SQX's daily equity from its running high, in R (positive). That curve is each day's **lowest** equity, open positions at their worst wick (`OPEN.md` #88), so this is the floating drawdown, not the closed one |
| `oos_worst_day_r`, `is_worst_day_r` | worst single server day of that equity, floating included, in R (negative): low to low, not start-of-day to low — a proxy for a firm's daily-loss rule, not the rule |
| `oos_worst_trade_mae_r`, `is_worst_trade_mae_r` | worst `MAE ($)` of any trade, in R (negative) |
| `oos_net_per_year_r`, `is_net_per_year_r` | closed net per year, in R |
| `oos_dd_over_net_year`, `is_dd_over_net_year` | `max_dd_r` / `net_per_year_r`: how many years of net the worst floating fall cost (1.5 = repaid in 18 months). **+inf when net ≤ 0** — never NaN, which a rule would read as a missing fact (limbo): a `<=` rule fails it. NaN only for a strategy without trades |

1R is the doctrine's fixed risk per trade (`assets/_build.yaml` `money_management.params.Amount`,
1,000 USD). It is nominal — the doctrine carries no stop — which is exactly what the MAE column shows.

**Three t's, three scales** (`knowhow/research/gate-t-scales.md`): `degradacion_t` is Lo's t on SQX's
daily curve (floating included) and reads ≈ 0.8× `trade_t`; before 2026-10-02 it was also compressed
by a units bug (annualised Sharpe inside the variance term) and capped at √(2·years). A scorecard
written before that date is on the old scale — never mix the two.

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
