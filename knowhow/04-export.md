# Export — trades, metrics, bars

## Trades

🔬 `-tools action=orderstocsv file=<folder> output=<dir> data=main` accepts a **folder** and exports
every `.sqx` in it in one JVM start — 231 strategies in ~4 min. Read-only; it needs no build and
touches no project state. Drive it with `bin/sqx-worker.sh run` (one-shot, worker stays stopped after).

### The `orderstocsv` schema — three traps

16 columns: Ticket, Symbol, Type, Open time, Open price, Size, Close time, Close price, Profit/Loss,
Balance, Sample type, Close type, MAE ($), MFE ($), Time in trade, Comment.

1. 🔬 **MAE/MFE are in ACCOUNT CURRENCY, not points.** Convert with
   `price = abs(MAE_$) / (Size * pointValue)`; `pointValue=100` for XAUUSD_Infinox. **`Size` varies per
   trade** (risk-based sizing), so the conversion must use each trade's own size — a fixed divisor is
   wrong. Verified: MAE_price always brackets the realised adverse move.
2. 🔬 **`Sample type` depends on how that strategy was last retested — check it, do not assume.** In
   the `SPP OOS` / `WFM` databanks every `data=main` row was `IST`, so the column was useless there and
   the window had to come from `Open time`. But the **`OOS` databank of the same project exports
   both**: `IST` = 2008.01.02–2017.12.29 and `OOS1` = 2018.01.02–2022.12.30, a clean split at the
   retest boundary. Where the labels are present they are the reliable IS/OOS key; where they are not,
   fall back to `Open time`. Either way a strategy's stored *main* result is whatever period it was
   last retested over — of 231 strategies in `SPP OOS`+`WFM`, 46 had a main result covering only
   **2018–2023**, so they contribute zero trades to a 2008–2017 study.
3. 🔬 The last row can be an **unfilled pending order** (`Close type=EndTest`, blank Close price / P&L /
   MAE). Drop rows with a blank close price.

🔬 **Costs are recoverable per trade** as `gross - reported P/L`, where
`gross = (close-open) * Size * pointValue`. On this install that measures a steady **$8 per lot per
side** ($16/lot round turn), matching `commissions=<Method type="SizeBased">8`. Spread
(`defaultSpread="10.0"`) is already inside the fill prices — it does **not** appear in that residual.
Overnight trades show extra drag (swap: long −73.42 pts, short +38.76 pts).

### Duplicates are real, but not what the name suggests

🔬 `SPP OOS` and `WFM` share strategy **names**, but the same name in the two databanks is usually a
**different** strategy — only 1 of 231 files was a true inner-XML duplicate. However, **45 of 231 have
byte-identical trade lists**: WFM re-exports the SPP OOS strategy with parameters
`makeExternal="true"` for optimisation, which changes the XML hash but not the logic. **For any pooled
statistic, deduplicate on the exported trade list, not on the XML hash or the name.**

### `data=all` gets the cross-market retest results, in one CSV per strategy

🔬 A strategy retested on additional markets **stores every market inside its own `.sqx`**: entries
`Results/AdditionalMarket: <feed>: <feed>/dailyEquity.bin`, `<Result resultKey="AdditionalMarket: ...">`
blocks in `settings.xml`, and one `orders.bin` (`SQOrderFileFormat:11`) holding every result's orders
tagged by result key. Verified on `EURUSD/databanks/RetestMarkets - Structural/Strategy 10.11.23.sqx`
(main EURUSD plus USDJPY, USATEC and XAUUSD).

🔬 `data=all` writes all of them into **one CSV per strategy**, as contiguous blocks in result order —
main first, then each AdditionalMarket. **The `Symbol` column is the separator**; `Ticket` restarts at
1 in every block, so it is not a key across markets. `orders.bin` never has to be parsed.
`sqx/export/export_retest.py` does the split. Measured on that strategy: 301 / 256 / 193 / 393 rows,
each block with its own date range, all four `Sample type=IST`.

🔬 **A market whose strategy never traded there produces no file at all.** The split is driven by the
`Symbol` values actually present, so `trades/<feed>/<strategy>.csv` simply does not exist when that
strategy fired zero times on that market. Measured 2026-09-14 on `XAUUSD / Retest Markets - Family`:
of a 30-strategy sample, **2 have no `XAGUSD_DukasM1_Infinox` file** while all 30 have gold and
Brent. Anything iterating (strategy × market) has to treat the absence as a result about the
strategy, not as a missing input — `crossmarket/explorer/analysis.py` records it as `missing` and
reports it. On the full 757-strategy databank expect roughly 50 such gaps.

🔬 **`stage()` takes a `limit`**, added 2026-09-14: `export_retest.py --limit 30` stages a
**reproducible random sample** (seed 20260914) instead of all 757. Random rather than the first N,
because a databank is written in build order and its first strategies all come from one generation
run. Both export commands drive the **worker**, never the master, so they are safe with the master
GUI open.

🔬 **Exit types in the XAUUSD generated fleet**, measured over 92,329 trades of that 30-strategy
sample: `Exit After X Bars` **78.0%**, `Exit Signal` **16.6%**, `End Of Friday (Time)` **5.4%**. The
Friday close lands on **Friday 21:00** (832 of 838 observed exits; the rest 21:02 and 21:16). That
matters to any study that places synthetic trades: the Friday close is a calendar rule a null can
reproduce exactly, and `Exit Signal` is not reproducible without reading the `.sqx`.

🔬 **The whole databank is long-only.** All 92,329 trades of that sample are `Type=Buy`. Any code
computing `log(exit/entry)` is silently wrong on a short, so assert rather than assume.

🔬 **A trade's P/L can be rebuilt from the bars almost exactly, which is what makes dollar
statistics possible for synthetic trades.** With the open-to-open convention,
`(Open[exit] - Open[entry]) * Size * pointValue` against the reported `Profit/Loss` gives
**r = 0.9996** on XAUUSD, XAGUSD and BRENT (2,031 / 2,005 / 1,321 trades, 2026-09-15). The residual
is the cost plus the swap, ~20 $ per trade on the metals and ~29 $ on Brent, and it is recovered per
trade as `gross - reported` rather than assumed. `pointValue` itself is measured from the trades by
least squares (`pricing.point_value`), not read from the asset file, because a cross-market study
prices instruments the base asset's file knows nothing about.

Consequence: a random-entry null can be priced **in the account currency with the real trades' own
sizes and costs**, so net profit, drawdown, Ret/DD, Sharpe and profit factor are all comparable
against SQX's own numbers instead of against an abstract normalised statistic. That is what
`strategies/crossmarket/simulate/metrics.py` does.

🔬 **The fill convention is open-to-open**: entry at the `Open` of the entry bar, exit at the `Open`
of the exit bar. Reconciled against 1,101 real XAUUSD H1 trades with a **median price error of
exactly 0.0** against `bars_H1.csv`. `strategies/analysis/pricing.reconcile()` re-derives it per
market rather than assuming it, since a mismatch would silently invalidate any comparison against
prices computed in Python.

🔬 **The point value is recoverable per market, and does not need an asset file.** Regressing
`Profit/Loss` on `(close − open) × Size` gives the slope as point value at R² ≈ 0.999; the residual is
swap. Measured on `Strategy 24.14.35` of `Retest Markets - Family`: **99.8 for XAUUSD** (configured
100), **5002 for XAGUSD** (a 5,000-ounce contract) and **100.0 for BRENTCMDUSD**. This matters because
a cross-market study prices markets the base asset's `assets/*.yaml` knows nothing about — silver and
Brent have no file at all. `strategies/crossmarket/mechanics/pricing.point_value()` does it.

🔬 **Not every entry lands on a bar open.** On the 36-strategy XAUUSD export, 573 of 48,894 entries
(1.2%) fall inside a bar; on the EURUSD retest strategy above, entry times are minute-level
throughout (`2008.01.07 11:12:00`) — those are pending orders filled intrabar. A pending fill is a
price-conditional selection, so any study that places synthetic trades has to check this share per
market before trusting the comparison.

🔬 **The share is much worse on the additional markets than on the base one.** `Strategy 24.14.35`
of `Retest Markets - Family` (M30) fills on a bar open 98.3% of the time on gold but only **91.8% on
silver and 91.4% on Brent** — same strategy, same pending orders, different liquidity. Verified that
these are genuine intrabar fills (`02:01`, `13:20`, `18:31`) and not gaps in the bar file: zero
entries sit on the `:00/:30` grid without a matching bar. A cross-market study therefore has to test
this **per market**, because the base asset's number does not predict the others'.

🔬 **Check bar-open alignment against the bar index, not the clock.** `minute == 0` is right for H1
and silently wrong for M30, where a bar also opens on the half hour. `core.trades.on_bar_open()` tests
membership of the real bar index, which works at any timeframe.

### `data=all` also gets every cell and every step of a Walk-Forward Matrix

🔬 A WFM strategy's `orders.bin` holds the orders of all 31 results -- the main backtest plus the 30
matrix cells -- and `data=all` writes them into one CSV per strategy as contiguous blocks in the
order `settings.xml` lists the results. Measured on `XAUUSD/WFM/Strategy 10.16.68`: **60,151 rows**
in one file.

🔬 **The `Symbol` column cannot separate them.** Every cell trades the same symbol, so the
cross-market trick from the retest export does not apply. The separator is `Sample type`: the main
block is `IST` throughout, and each cell block **opens with `IS`** -- the backtest of its first
optimisation window -- then turns to `OOS1` for the walk-forward steps and never goes back. Cutting
where `Sample type` becomes `IS` gives exactly 30 blocks in cell order. `core/wftrades.chunks()`.

🔬 **Assign a trade to its step by the next step's `runFrom`, never by its own `runTo`.** `runTo` is
a date at midnight, so testing `runFrom <= t <= runTo` silently drops every trade taken later that
same day -- 81 of 58,500 on the strategy this was checked against, always one or two per step, which
is small enough to look like rounding and is not. A `searchsorted` over the `runFrom` values gets it
exact. Verified against SQX's own stored `oos_NumberOfTrades` for all 30 cells: **0 discrepancies in
39,873 trades**. `core/wftrades.check()` writes that comparison out rather than asserting it, because
a date-based split of a 60,000-row file has to be provable.

🔬 The whole thing is one command: `python3 -m sqx.export.export_wfm --project XAUUSD --databank WFM`.

## SPP — the Sys. Param Permutation cross-check

🔬 **There is no CLI verb for it.** `sqcli -help` offers nothing for optimization or cross-check
results, and `-tools action=orderstocsv data=all` covers only what `settings.xml` lists under
`Results` — main plus AdditionalMarket. The SPP panel lives entirely inside the strategy's
`optimizationProfile.bin` (`01-file-formats.md`), so it is read from the file, not exported:
`python3 -m sqx.export.export_spp --project XAUUSD --databank "SPP IS"`.

🔬 **SPP permutations have no trades to get** — established from `SQStats.serialize` itself, not
inferred (`01-file-formats.md`). Each permutation is its parameter string plus a numeric-only stats
blob; no order list is ever written. Asking SQX for "the trades of the cross-check" is therefore not
a matter of finding the right command. The trades that do exist are the strategy's own main backtest,
and `data=main` gets them.

🔬 **What you can get instead is the whole permutation table**, once *"Don't store data for 3D charts
in Optimization profile"* is off and the SPP is re-run: one row per permutation with its parameters
and its 152 statistics. 📓 Done for real on 2026-09-10 -- `XAUUSD/SPP IS` now yields **21,205
permutations across five strategies**, 3,940 to 4,523 each, and `export_spp.py` already wrote them to
`permutations.csv` and `permutation_params.csv` without a code change. Each permutation carries one
sample, so this is an in-sample surface: it does not pair an IS result with an OOS one. That is strictly more than the SQX panel shows — it gives arbitrary
percentiles instead of the stored median, cross-metric joins, and the parameter surface
(`NetProfit` grouped by one parameter's value), which no SQX screen displays.

### Two SPP runs cannot be paired for a Walk Forward Correlation

🔬 2026-09-19, `XAUUSD/SPP IS` (task 13, 2008-01-01 to 2017-12-31) and `XAUUSD/SPP OOS`
(task 14, 2018-01-01 to 2022-12-31): the same 5 strategies, a byte-identical
`strategy_Portfolio.xml`, the same permuted parameter list and identical SPP settings
(`MaxTests` 15000, +/-30 %, 20 steps, *Recommended*). They still cannot be joined permutation by
permutation, for two independent reasons:

- **SPP samples, it does not walk a grid.** Every permutation changes *all* parameters at once, and
  the full grid is 2.7e7 to 3.2e11 combinations of which only ~12,000 are drawn.
  🔬 **Measured, both runs re-done with the permutations stored, 2026-09-19:** 62,997 IS
  tuples against 63,114 OOS tuples share **5**. Per strategy the observed overlap equals the
  birthday collision count of two independent uniform draws almost exactly -- expected 5.05 against
  5 observed on `Strategy 17.9.39` (grid 2.7e7), 0.03/0.20/0.00/0.00 against 0 on the other four
  (grids 7.2e8 to 3.2e11). The sampler is **not** seeded to repeat: nothing is shared but chance.
  🔬 It is not a formatting or step problem either -- the per-parameter value domains are
  **identical** in the two runs (same 7 to 20 values, same strings), and no run repeats a tuple of
  its own. The grid is the same; only the ~12,000 points drawn from it differ.
- **The draw is never close to the original either.** Every permutation changes at least 2 to 6
  parameters, so even the few tuples that do collide sit far out in the space: an SPP sample cannot
  describe the neighbourhood of the optimum, which is where an overfitting diagnostic lives.

📓 Each permutation carries **152 statistics**, and the 5 collisions do pair correctly
(`Strategy 17.9.39`, e.g. IS NetProfit 23,608 / OOS 10,789 on one tuple) -- the join itself is
sound, there is simply nothing to join. Watch the storage setting when reading any of this:
*"Don't store data for 3D charts"* ticked leaves only medians and histograms, and the run has to be
repeated to get the permutations back.

### Shrink the grid and two SPP runs DO pair — measured

🔬 2026-09-19 20:11, `XAUUSD/SPP IS` gained two re-runs (`Strategy 1.19.29(1)`,
`Strategy 4.33.46(1)`) under different SPP settings -- `Steps` 12, `MaxTests` effectively unlimited,
and only Periods + Constants + ExitParamsUsed permuted, which freezes 4 of 10 parameters at a single
value. The consequence is decisive:

| | parameters moved | grid | permutations stored | coverage |
|---|---|---|---|---|
| `Strategy 1.19.29` (20 steps, Recommended) | 10 | 6.0e9 | 12,857 | 0.0002 % |
| `Strategy 1.19.29(1)` (12 steps, 3 classes) | 6 | **6.27e4** | **41,720** | **66.5 %** |
| `Strategy 4.33.46(1)` | 5 | **4.03e4** | **34,390** | **85.3 %** |

At that coverage two independent runs of the same settings share `n_IS x n_OOS / grid` = **~27,750 and
~29,300 tuples** -- 66 % and 85 % of each run, against 5 tuples in 63,000 before. The pairing problem
is not a property of SPP; it is a property of grid size against sample size. **Saturate the grid and
SPP becomes a WFC instrument**, with all 152 statistics per point and no variant machinery at all.

🔬 **The lever that saturates a grid is the shifts, then `Steps`.** Measured over the 5
XAUUSD strategies: freezing every `ParamTypeShift` (there are 3 to 6 per strategy, 7 levels each)
divides the grid by 7^k -- `Strategy 41.5.25` goes 1.39e11 -> 1.18e6, `Strategy 17.9.39`
2.06e6 -> 6.0e3, `Strategy 1.19.29` 6.02e9 -> 3.58e5. After that the grid is `(levels)^k` over the
k surviving parameters, so the setting that saturates a budget of n permutations is
**`Steps` ~ n^(1/k) - 1**: k=4 wants ~10 steps, k=6 wants ~4, k=7 wants ~3. Integer ranges cap it
further (`IsBars1` = 3 can only ever yield 5 values), which errs toward saturation.

🤔 Two things stay open. The permutation count saturates at 66 % rather than reaching the
full grid (21,000 of 62,720 tuples never appear) and it is not known whether SQX excludes them
systematically -- if it does, both runs exclude the same ones and the real overlap is nearer 100 %.
And the OOS task must be given the **same** SPP settings before it is re-run; as of 2026-09-19 task
14 still carries `Steps` 20 / `MaxTests` 15000 / Recommended, so its grid is a different one.

### Unpaired SPP runs still answer "which parameters matter" -- and half of the WFC

🔬 Two SPP runs that share no tuples are still two random samples of the same parameter
space, so each supports a **first-order sensitivity** estimate on its own. Grouping the permutations
by one parameter's value and taking the share of Ret/DD variance that falls between those groups
(eta-squared, >= 100 trades) over the 11-13k permutations of each XAUUSD run:

| strategy | parameters | eta2 >= 0.01 in either window | grid before | after |
|---|---|---|---|---|
| `Strategy 17.9.39` | 8 | **3** | 2.3e7 | **7.2e2** |
| `Strategy 23.16.37` | 11 | 6 | 3.2e11 | 6.3e6 |
| `Strategy 1.19.29` | 10 | 8 | 6.0e9 | 4.7e7 |
| `Strategy 41.5.25` | 12 | 9 | 1.4e11 | 4.1e8 |
| `Strategy 4.33.46` | 9 | 7 | 7.2e8 | 1.0e8 |

Two or three parameters carry most of the variance every time -- `DICrossPeriod1` 0.28 and
`DICrossShift1` 0.23 on `17.9.39`, `KCBarCloseserShift1` 0.41 on `41.5.25` -- and the rest sit under
0.01. Freezing those shrinks the grid by 7x to 51,000x, which is what turns a saturated paired run
from impossible into routine.

🔬 **The marginal profile is a WFC that needs no pairing at all.** `E[Ret/DD | parameter =
v]` is estimable in each run separately (every other parameter is randomised around it), so the two
runs give two curves over the same values, and their rank correlation says whether the parameter's
response replicates out of sample. Measured: `Strategy 4.33.46` / `ATRPrcRnkCrsDwnATRPrd1` **+0.95**
with eta2 0.17/0.14 -- it matters and it holds. Against that, `Strategy 17.9.39` /
`DICrossPeriod1` is the single most influential parameter in sample (eta2 0.28) and its profile
correlation is **-0.47**: what was best in 2008-2017 is among the worst in 2018-2022.

🤔 eta-squared is first-order only -- a parameter acting purely through an interaction reads
as 0. For "does nothing at all", the exact-duplicate test in `01-file-formats.md` is the definitive
one.

### Sequential optimisation pairs perfectly and still is not a WFC

🔬 2026-09-19, `XAUUSD/Seq. Opt. IS` (task 15, 2008-2017) against `Seq. Opt. OOS` (task 16,
2018-2022), same 5 strategies, identical settings (+/-30 %, 30 steps, `ApplyToStrategy` false).
Unlike SPP this **matches**: the same 50 parameters on both sides, the `<Values>` grids identical
value for value, **1,507 (IS, OOS) fitness pairs** and no float or step mismatch anywhere.

🔬 **But 1,356 of those pairs are not the same strategy on both sides.** The scan is chained
(`01-file-formats.md`), so parameter k is measured with parameters 1..k-1 at the values *that run*
chose -- and the two runs choose differently: the `BestValue` agrees on only **1 or 2 of each
strategy's 8 to 12 parameters**. A point labelled `DICrossPeriod1=64` is the tuple
(`CBlock`=IS's pick, 64, rest original) in one databank and (`CBlock`=OOS's pick, 64, rest original)
in the other. Same label, different strategy.

🔬 **What survives is the chain up to its first divergence**: while the two runs have
picked the same values, the context is identical and the points are genuinely the same tuples. That
prefix is short -- 0 or 1 parameter -- so **7 scans, 211 pairs**, of which two scans are inert
(`CBlock_SqzMmnInt21`, flat fitness across all 31 values, which is also why its `BestValue` agrees:
a flat curve gives the same stable-area centre in both runs), leaving **5 informative scans and 150
pairs, one scan per strategy**. That is a line through the original per strategy, one scalar
(fitness) per point: a sensitivity curve, not an optimisation surface.

🔬 **The scatter is 1,507 points, not 50** -- 50 is the number of axes, each contributing 30
or 31 paired points. Pooling them all into one cloud is a Simpson trap: the pooled Spearman is
+0.292, but per strategy it runs from **-0.05 to +0.74**, and each scan sits at its own fitness level.
Demeaning the ranks within each scan -- which is what averaging the per-scan rho does -- gives
**+0.235 over 1,415 points**. ⚠️ **The >= 100 trades filter cannot be applied here**: the
sequential-optimisation XML stores fitness and nothing else. Only the 26 IS and 32 OOS points whose
fitness is exactly 0 can be identified as degenerate.

🔬 **The `Fitness` a sequential optimisation stores is the databank `Fitness` column, and
above 100 trades it is Ret/DD.** The fitness at the first scan's original value equals the SPP
profile's `Fitness` stat for the same strategy to float32 precision on all 5 strategies, so the two
cross-checks report the same scalar. Against the SPP permutations of `Strategy 17.9.39`, restricted
to the 10,935 permutations with >= 100 trades, Spearman(`Fitness`, `ReturnDDRatio`) = **+0.999**
(+0.978 against `ProfitFactor`), and +0.999 again on the OOS run's 11,262. Below that trade count the
relation breaks down (+0.769 unrestricted) -- a handful of trades makes any ratio meaningless. So a
study over the sequential-optimisation surface is a study of **Ret/DD ranks**, not of an opaque score.

🔬 **A rudimentary WFC does come out of it, and it is positive.** Per scan, Spearman of the
30 IS fitness values against the 30 OOS ones:

| | scans | pooled rho (Fisher-z) | 95 % CI | positive |
|---|---|---|---|---|
| clean (first link only, one per strategy) | 5 | **+0.335** | +0.10 to +0.54 | 5/5 |
| every non-inert scan, contaminated included | 47 | **+0.309** | +0.14 to +0.46 | 35/47 |

The two agree, which is the argument for reading the 42 contaminated scans at all: the chain's
divergence adds noise without moving the estimate. 🤔 Three things it is not -- it is a star of
axes through the original, so it says nothing about *joint* overfitting; the 30 points of a scan are
strongly autocorrelated (lag-1 up to +0.89, effective n **9 to 33**), which is why a single scan's CI
spans zero; and part of any positive rho is mechanical, since a parameter that changes exposure moves
IS and OOS profit together. Naming a threshold for "high" without a null built from random-entry
variants would be false precision.

🤔 A WFC needs the *same* tuples scored on two windows, and no SQX cross-check gives that at
scale: sequential optimisation gives one clean line per strategy and 49 contaminated ones, the
Optimize task keeps only its top `maxOptimizations` results (truncating the surface on IS rank,
which attenuates the very correlation being measured), and the WFM stores the parameters it picked
per step, not the population. The route that cannot fail is to draw the tuple list **once** and
score it twice: parameter values are plain `<variable><id>NAME</id><value>N</value>` entries in
`strategy_Portfolio.xml`, so N variants can be written as N `.sqx`, dropped in one databank and
retested once over 2008-2022 with the OOS cut at 2018 -- a `.vw` emitting sampleType 10 and 20 then
puts the IS and the OOS score of each tuple on the same row, paired by strategy identity rather
than by matching values.

## Bars

🔬 `-data action=export symbols=<SYMBOL> timeframe=<TF> ...` exports OHLC as CSV. **The symbol is
`XAUUSD_DukasM1_Infinox`, NOT `XAUUSD_DukasM1_Infinox_M30`** — the timeframe is a separate argument.
Passing the suffixed name fails with `Symbol ... not found.` Output lands as
`<symbol>-<TF>-No Session.csv`, and a second export in the same JVM overwrites rather than adding, so
run one timeframe per invocation (`-run file=cmds.txt` works but names both outputs the same).

## Databank metrics, with the IS/OOS split

🔬 **`sampleType` is decoded**: **10 = in-sample · 20 = out-of-sample · 127 = full period.** Read off
the shipped views — `Modo Sergiogus - OOS.vw` uses 20 for every performance column and 127 only for
sample-independent ones (Symbol, TimeFrame, indicators).

🔬 **A custom `.vw` can emit the same metric at several sample types in one export.** Put a file in
`user/settings/views/databanks/<Name>.vw` and pass `view=<Name>`; column `name=` is free text, so
`name="ProfitFactor (IS)"` at `sampleType="10"` and `name="ProfitFactor (OOS)"` at `20` give paired
columns on one row per strategy. 46 metric classes exist. The export also prepends `Strategy Name` and
`Filters result` (PASSED/FAILED) automatically. Project copies of the views live in `sqx/views/`.

### The route, and why it is convoluted

`-databank action=export` only works on the instance that **holds** the project, and the master's CLI
is dead while its GUI is up. So: **stage the `.sqx` into the worker's own
`Retester/databanks/Results/`, start the worker, export, stop it.** Copy while the worker is stopped,
or its next sync fights the copy.

🔬 **Two asynchronous steps make the obvious one-shot form fail silently:**

1. `-databank action=load ... folder=<dir>` **returns before it has loaded anything.** A `count` in the
   same `-run` batch reports `Loaded 0 strategies`, and an `export` in that batch writes a
   **header-only CSV with no error**. The strategies do appear on disk at shutdown, so it looks like it
   worked.
2. The startup sync-from-files is *also* async, so a fresh one-shot `sqx-worker.sh run -databank
   action=export` immediately after **also** yields a header-only CSV.

**Therefore: do not use `sqx-worker.sh run` for a databank export.** Start the worker as a daemon and
poll `-databank action=count` over HTTP until the reply contains `Records:` — the port opens and
answers `Error: CLI not ready.` for ~20 s before commands work, and strategy loading finishes later
still. `sqx/export/export_metrics.py` does exactly this.

🔬 A databank created with `-databank action=create` is **not** picked up by the startup
sync-from-files — only databanks already registered in the project are. Staging into an existing
`Results` databank works; creating `MetricsTmp` and loading into it does not.
