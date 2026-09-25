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

### What the project actually stores — measured 2026-09-21

🔬 **Resampling M1 in pandas reproduces SQX's own export of a higher timeframe exactly.** On
`XAUUSD_DukasM1_Infinox`, 7,708,823 M1 bars resampled to M30 give **274,832 bars against SQX's
274,832**, identical index, and `max|diff| = 0.000000` on Open, High, Low and Close. Only `Volume`
differs, on **13 of 274,832 bars by at most 2 units** — SQX's own rounding when it aggregates.
Consequence: **M1 is the only bar data worth storing**; M30/H1/H4/D1 are caches, not data, and
`core/barstore.py` builds them on first use. Reading M1 costs 0.78 s from Parquet against 5.57 s
from CSV, and each resample 0.3–0.4 s, so a cold timeframe is ~1.2 s and a cached one 0.02 s.

🔬 **float64 compresses SMALLER than float32 under zstd** on this data — 6.71 MB against 7.08 MB for
the same 274,832 M30 bars. A two-decimal price has a regular bit pattern in float64 that the
rounding to float32 turns into mantissa noise. There is no precision-versus-size trade to make here:
keep float64 everywhere, it is also cheaper.

🔬 **The per-export `bars/` directory was dead and is gone.** `export_trades.py` wrote
`raw/<P>/<D>/<date>/bars/bars_<TF>.csv` and **no module ever read it** — every consumer goes to the
shared library. It was also worse than the library copy: 228,979 bars from 2007 against 274,833 from
2003, different md5. Removed 2026-09-21 along with 29 MB of such copies.

### The trade export: 12 columns carry everything, 4 are derivable

🔬 Measured on `Strategy 1.19.29` (763 trades) and re-verified packing **757 strategies / 960,705
trades** with zero discrepancies on every kept column. Of the 16 columns `orderstocsv` writes:

| dropped | why | proof |
|---|---|---|
| `Ticket` | `= row index + 1`, and Parquet preserves row order | sorting by (`Open time`,`Close time`) reproduces it exactly on all 5 strategies checked |
| `Time in trade` | `= Close − Open`, and stored as text (`"2h 0m"`) | 26 distinct values |
| `Comment` | empty | 763 of 763 null |
| `Symbol` | constant per file → goes to the manifest | 1 distinct value |

⚠️ **`Symbol` is only droppable under `data=main`.** Under `data=all` it is the ONLY separator
between the market blocks, so `tradestore.pack(per_market=True)` keeps it. Getting this wrong makes
a cross-market retest unsplittable.

⚠️ **`Ticket` is only droppable while row order carries it.** `tradestore.ordered()` checks per file
— open-time sorted, no duplicate open times, no overlapping positions — and keeps `Ticket` for any
file that fails, recording it in the manifest. A pyramiding strategy or two entries on the same bar
would fail it. On the 757-strategy XAUUSD fleet, **zero files failed**: it is single-position
throughout, which is itself a fact about that fleet.

`Balance` is derivable too (`100,000 + cumsum(P/L)`, max deviation 0.17 over 763 rows, pure rounding)
and is **kept by the owner's decision**, not because it carries information.

🔬 **Packing moves the cost from time to peak memory, and that is a real trade.** Loading the
757-strategy export as monteCarlo streams went from **5.2 s / 266 MB peak RSS** (757 CSVs) to
**1.0 s / ~620 MB** (one Parquet). The bytes on disk and in the frames both fell — 74 MB of frame
against 406 MB — but Arrow's decompression buffers cost ~270 MB of transient RSS for a 20.5 MB file,
and `to_pandas(split_blocks=True, self_destruct=True)` only claws back 30 MB of that. Left as is:
the simulation phase dominates the run and this machine has the RAM. Anything memory-bound reading
these should read per strategy (`tradestore.read(path, name)`) rather than the whole export.

⚠️ **Keep the packed text columns categorical.** Widening them to object costs **326 MB against
74 MB** on that export. `core.trades.cost()` therefore does `.astype("object").map(SIDE)` on `Type`
itself — mapping a categorical returns a categorical, which then refuses to multiply.

🔬 **The packing is worth 8.7×.** 179 MB of CSV for 757 strategies becomes **20.5 MB** of one typed
zstd Parquet with the text columns as categories. Reading all 960,705 trades takes **0.16 s** against
about 3.9 s for the 757 CSVs. Reading ONE strategy out of it costs 0.032 s against 0.005 s for its
own CSV — the filter scans the file — so anything per-strategy should read once and split with
`tradestore.by_strategy()` rather than re-reading.

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

🔬 **A `data=all` retest export cannot tell you where the project's OOS starts.** Confirmed again
2026-09-21 on `XAUUSD / Retest Markets - Family`: all 1,124 gold, 913 silver and 842 Brent rows of
`Strategy 24.14.35` carry `Sample type = IST`, including the 351 gold trades that fall inside the
project's own out-of-sample range. The split has to be read from the project and declared:
`<OutOfSample><Range dateFrom="2018.01.01" dateTo="2022.12.31"/>` lives in `Build-Task3.xml` inside
`XAUUSD/project.cfx`, and `strategies/crossmarket/assets/_markets.yaml` carries it as `out_of_sample` for
that study. Reading the boundary off `Open time` works only because the range is known first — the
data volunteers nothing.

🔬 **On gold M30 the recorded entry price sits exactly 0.05–0.06 above the bar open, and the exit
sits on it.** Measured 2026-09-21 over the 1,055 grid-locatable gold trades of `Strategy 24.14.35`:
every single entry error is 0.05 (989 of them) or 0.06 (66), every exit error is 0. That is the
**entry-side spread on a Buy** — filled at ask, closed at bid — baked into the fill price rather than
charged as commission. The same export gives a median error of exactly **0** on silver and on Brent,
so it is a property of the `XAUUSD_DukasM1_Infinox` feed, not of the exporter.

Two consequences, and the second is the one that matters:

- Any check that asks "does a fill convention reproduce SQX's prices" reports a non-zero median on
  gold. It is **not** a wrong convention: open-to-open is still the winner by an order of magnitude,
  and 0.05 on a ~1,800 price is 2.8 bps, or 0.023 ATR. `crossmarket`'s `fill_mismatch` fired on every
  gold window over this until 2026-09-21; it now judges the error in median-ATR units against
  `diagnostics.max_fill_error` and a constant offset lives far below it.
- **The study is still priced consistently, because the cost is recovered rather than assumed.**
  `charged = gross(bar opens) − reported P/L` works out to `0.05 × Size + commission`, so the spread
  lands inside the per-trade cost every random run also pays; and `mean_r` is bar-open-to-bar-open on
  both sides, so it never sees the 0.05 at all. Real and null are on the same pricer either way.

🔬 **SQX executes this fleet on the logic timeframe's bar opens, and nothing happens inside a
bar.** Measured 2026-09-21 over `raw/XAUUSD/MC_Trades/2026-09-19`: **757 strategies, 960,705 trades,
M30**.

| what | measured |
|---|---|
| `Close type` values present | `Exit After X Bars` 720,874 · `Exit Signal` 187,853 · `End Of Friday (Time)` 51,978 |
| `Stop Loss` / `Take Profit` / trailing exits | **zero, in the whole fleet** |
| \|exit price − its bar's Open\| | median **0.0000**, p99 0.0100, **max 0.0100** |
| strategies whose median exit error is non-zero | **0 of 757** |
| \|entry price − its bar's Open\| | median **0.0800**, max 0.0900 — the entry-side spread, constant |

The consequence for any study that reprices these trades: **the logic timeframe's bar grid is the
correct execution grid**, and a finer one is not an improvement. Pricing on M1 would put entries and
exits on M1 bar opens SQX never used and would *create* a fill mismatch where there is none. The day
a strategy carries a stop, a target or a trailing, exits stop landing on bar opens, that median exit
error goes non-zero, and only then does M1 execution become the right fix —
`crossmarket/mechanics/pricing.reconcile()`'s exit-side median is the instrument that decides it, and
today it reads 0 on 757 of 757.

🔬 **An entry stamped inside a bar is a clock artefact, not a pending-order fill.** Same measurement:
4,613 of the 960,705 entries (0.48%) carry an `Open time` that is not a 30-minute boundary. Their
price distribution is **identical** to the 956,092 that are:

| | n | median price − bar Open | p1 | p99 | max abs |
|---|---|---|---|---|---|
| stamped late | 4,613 | +0.0800 | +0.080 | +0.090 | 0.090 |
| stamped on the open | 956,092 | +0.0800 | +0.080 | +0.090 | 0.090 |

**Not one** of the 4,613 sits outside `[0, 0.10]`. They entered at their own bar's open price and
were merely timestamped a few minutes late. Confirmed independently on the retest export
(`Retest_Markets_-_Family`, `Strategy 24.14.35`): gold's 19 late entries land on minute 1 and 31
only, all at bar open + 0.05; silver's 72 and Brent's 67 scatter across the minutes and are all at
bar open + 0.000 — the same offset their on-time entries carry. So a check that reads "share of
entries landing on a bar open" off the **clock** measures a stamping quirk;
`crossmarket`'s `diagnostics.min_on_open` does exactly that, and on this data it is measuring nothing
real. Read the **price** against the bar's open instead, which is what the question actually is.

🔬 **A zero-duration trade is a same-instant entry and exit, not a fast intrabar move.** 12,824 of
960,705 (1.33%); in the retest export, 69 of 1,124 on gold, 69 of 913 on silver, 60 of 842 on Brent —
**all `Exit Signal`, all with `Open time` exactly equal to `Close time`**. On silver and Brent the
open and close prices are identical too (100%), so the P/L is pure cost (−18.6 $ and −26.9 $ mean);
on gold they differ by exactly the 0.05 spread (−16.3 $ mean). No interval exists at any resolution,
so no finer timeframe recovers one. They are real trades with real cost and they belong in the
backtest's own numbers; they are simply invisible to any test that needs a duration.

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
`permutations.csv` and `permutation_params.csv` without a code change (since 2026-09-23 the two
are one wide `spp.parquet`: parameters as columns, statistics beside them — 49 MB → 6 MB, and
a reader that needs four columns reads four). Each permutation carries one
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

### 🔬 A databank whose task ran ONE window fills ONE of the view's two blocks — and WHICH one cannot be assumed (2026-09-23)

A paired view emits every metric twice, at `sampleType` 10 (`(IS)`) and 20 (`(OOS)`). A task that ran
a single window fills one block and leaves the other at zero. **Which block is the one SQX designated
that task as, and two real retest databanks disagree:**

| databank | window it ran | block with the numbers | the other block |
|---|---|---|---|
| `XAUUSD/SPP IS` | 2007-12 → 2017-12 | **10 `(IS)`** — `DrawdownPct` 6.57 | 20 all zeros |
| `XAUUSD/SPP OOS` | 2017-11 → 2022-12 | **10 `(IS)`** — `DrawdownPct` 7.27 | 20 all zeros |
| `XAU_ISOOS_ejemplo/Results` | 2007-12 → 2017-12 | **10 `(IS)`** — `DrawdownPct` 6.58 | 20 all zeros |
| `XAU_ISOOS_ejemplo/OOS` | 2017-11 → 2022-12 | **20 `(OOS)`** — `DrawdownPct` 14.85 | 10 all zeros |

Both `SPP OOS` and `XAU_ISOOS_ejemplo/OOS` are retests over the same out-of-sample window, and they
put their numbers under opposite labels. Sample type 11 and 127 repeat whichever one is filled.

**So reading "Net profit (OOS)" from a two-task setup returns a zero about half the time, with
nothing failing.** The block has to be read off the data: `gate/collect.py::measured()` sums the
absolute values of the metrics the view emits at **both** types and takes the block that is not zero.

⚠️ **Compare only the paired metrics.** A view also emits structural columns at one type only —
`Param Count (IS)`, `DoF Ratio (IS)`, `TimeFrame (IS)` — and those carry a number whatever the task
ran. Counting them makes every databank look like it filled the `(IS)` block, which is the first
version of this detector and it was wrong.

⚠️ **Both blocks filled means the task ran its own internal split** (`XAUUSD/OOS`, `XAUUSD/MC
Trades`). Then neither half can be called "the retest" from outside, and `measured()` refuses rather
than guessing.

This is the metrics-side twin of the trades-side trap above: `Sample type` was `IST` for every row of
the `SPP OOS` and `WFM` exports for the same reason.

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

## Storage format — the saving is in the format, not in dropping columns

🔬 **Decided and applied 2026-09-23 — one typed Parquet per test and export** (the analysis with every
measurement: `docs/AgentPDFs/almacenamiento-datos-2026-09-23.md`). Five rules: the `.sqx` is the
source and an export is a projection; one file per test and export, never one per strategy (118
cross-market CSVs became one 4 MB `trades.parquet`); wide for parameters and statistics, long for
trades (the SPP's long parameter table was 34 MB in RAM for 21,205 × 8 numbers that are 6 MB wide);
`strategy`/`Symbol`/`Sample type`/`result`/`sample` categorical, money as `int32` cents or
`float32` where it already was; intermediates (`raw/` CSV, staged `.sqx`) die with the export.
`raw/` went from 346 MB and 270 files to 112 MB and 123. `metrics.csv` stays CSV: a person reads it.
📓 The three studies re-ran on the migrated data with identical verdicts (sppUltra, WFM) and the
cross-market readers reproduce `backtest.setting` on all three markets.

🔬 Measured 2026-09-20 on `raw/XAUUSD/SPP_IS/2026-09-10/`, 21,205 permutations x 154 columns.

| | size | factor |
|---|---|---|
| `permutations.csv`, 154 columns | 39.67 MB | 1x |
| **Parquet zstd, the same 154** | **5.72 MB** | **6.9x** |
| CSV, 29 curated columns | 9.87 MB | 4.0x |
| Parquet zstd, 29 curated | 1.51 MB | 26x |

**The format gives 6.9x with nothing discarded; curating the columns gives 3.8x more and is where
the regret lives.** The same holds for trades, more sharply (one strategy, 763 trades): CSV 134.2 KB
-> Parquet typed with all 16 columns 42.4 KB (3.2x) -> Parquet with 8 columns 29.8 KB (only 1.4x
more). Halving the columns buys almost nothing and costs `MAE ($)`/`MFE ($)`, which `strategies/`
uses and which cannot be reconstructed.

Rule that follows: **change the format, keep the columns.** For SPP especially, where the
permutation threw its trades away and those 152 numbers are all that will ever exist of that point —
recovering one column later means re-running SQX.

### What is safe to drop from an SPP export

🔬 Of the 152 metrics, **42 are constant across all 21,205 rows** and carry nothing: the four
`AddMarkets*Median`, `BestWF`, `EdgeDecayRatio`, `Parameters`, `SlopeRatio`, the three `TotalData*`,
and **34 unnamed `stat:f:NN` / `stat:i:7` / `stat:l:2-3` columns SQX never fills**. Of the 110 that
vary, **85 carry unique information**; 25 are redundant at |rho| > 0.999 within one window. The
eleven groups:

```
AHPR = AnnualPctReturn = AvgPctProfitPerYear = AvgProfitPerDay = AvgProfitPerMonth
     = AvgProfitPerYear = CAGR = NetProfit = NetProfitInPct
AnnualPctReturnDDRatio? = CalmarRatio?        AvgTrade = Expectancy
AvgTradesPerDay = AvgTradesPerMonth = AvgTradesPerYear = DegreesOfFreedom = NumberOfTrades
Drawdown = DrawdownPctOnInitial = MaxTSIntradayDrawdown = OpenDrawdown
DrawdownPct = OpenDrawdownPct    Exposure = ExposurePosition    Outlier = Outlier2
PayoutRatio = TSWinLossRatio     WinLossRatio = WinningPct      ZProbability = ZScore
```

⚠️ **That redundancy is intra-window and does not survive between windows of different length.**
`NetProfit` and `CAGR` rank identically inside one run; across a 10-year IS and a 5-year OOS they do
not, because total return grows with the horizon and the annualised one does not. That is the same
sqrt(T) bias that makes `Ret/DD` unusable for comparing windows. **Keep both.**

### RExpectancy carries sentinels, and they win the argmax

⚠️ 🔬 `RExpectancy` stores **99999.0** on 3 rows and **-1.0** on 15, all of them permutations with
about one trade — SQX's "undefined", not a measurement. They are 0.08 % of the grid, which is exactly
what makes them dangerous: **take the maximum of `RExpectancy` over 5,000 variants and those three
rows win**, so a parameter-selection rule ends up decided by one-trade permutations. No other metric
of the 41-column export carries them. `core/surface/dedupe.drop_sentinels` filters `|v| > 100` before
any ranking.

### Two columns carry a literal question mark in their name

🔬 `CalmarRatio?` and `AnnualPctReturnDDRatio?`. Asking for them without the `?` yields a column of
NaN with no error.

### Eta-squared cannot decide which parameters are inert, and the duplicate test can

🔬 Measured 2026-09-21 on `XAUUSD/SPP IS` (2026-09-10 export), reading `ReturnDDRatio`.

`CBlock_SqzMmnInt21` on `Strategy 17.9.39` gives **217 groups of tuples differing only in it, and
all 217 produced an identical backtest** — proof that it never moved anything. Its eta-squared is
nonetheless **0.0173**, above any freezing threshold one would pick. `IsBars1` scores **0.0016** and
is demonstrably live, with 1 of 188 groups identical.

The cause is that **an SPP samples unbalanced**: each level of an inert parameter met a different
mix of the other parameters, so the spread between group means is confounding rather than effect.
**Eta-squared of an inert parameter is not zero; it is biased upward.**

Consequence for any design built on an SPP: **freeze on the duplicate test, allocate levels with
eta-squared.** Using eta-squared to freeze would have kept a dead parameter in the design and thrown
out a live one, in the same table.

⚠️ And eta-squared is meaningless as a single number, because it depends entirely on the metric:
the same `DICrossShift1` explains **7.6 % of NetProfit, 23.6 % of Ret/DD and 78.5 % of trade
count**. Report it as a table over several metrics and name the one the decision was taken on.

🔬 **Inertness belongs to the strategy, not to the block.** The same `CBlock_SqzMmnInt21` gives 108
groups on `Strategy 41.5.25` of which only **106** are identical. Test it per strategy; never carry
the call across.

🔬 **The pairing failure, with a number.** `Strategy 17.9.39`, the 2026-09-19 paired export: the IS
run holds 11,598 rows and the OOS run 11,662, and they share **6 `param_key` values**. That is the
measurement behind "two SPP runs cannot be paired", and the reason the 5,000 designed variants are
the main route rather than a fallback.

🔬 On that same paired export, `DICrossShift1` explains **34.2 % of the in-sample Ret/DD variance
and 68.2 % of the out-of-sample** — confirming the protocol's headline figure of 67.6 %. It is the
most important parameter out of sample, and it is a shift, i.e. one of the parameters an SPP
configured the usual way freezes by default.

## WFM — what the Walk-Forward Matrix export does and does not hold

🔬 Measured 2026-09-21 on `raw/XAUUSD/WFM/2026-09-10/wfm/` (2 strategies, 60 cells, 720 steps).

⚠️ **`is_Fitness` and `oos_Fitness` are 0 on every step.** SQX stores fitness only at cell level, as
`fitness_is` / `fitness_oos` in `cells.csv`. The per-step columns exist, are named the obvious
thing, and are zeros — an analysis reaching for them correlates nothing and gets a NaN, or silently
reports whatever a constant input produces. Read a real metric per step.

⚠️ **The last step of every cell runs past the end of the data.** 60 of the 720 steps carry
`future=True`; cell 6x20 of `Strategy 1.19.29` ends with a step running **2025-12-31 to
2027-08-20**. Their out-of-sample statistics are computed on history that does not exist.

🔬 **The window geometry, which decides what may be pooled.** Within a cell, the run windows are
**disjoint and consecutive** — 0 overlaps across all 60 cells — so a cell's steps are separate draws
in time. The optimisation windows **overlap by 6.5 of 8.2 years, 79 %**. And every cell re-splits
the same 10-14 years of history, so 30 cells are 30 views of one dataset rather than 30
observations. **The cell is the unit**; pooling the 660 steps into one correlation reports an
interval several times narrower than the data supports.

🔬 **Two strategies in one export do not share a parameter list**, so the wide frame from
`params.parquet` (wide since 2026-09-23) carries all-NaN columns per strategy. `NaN != 0` is True in pandas, so any step-to-step
comparison that does not drop them counts a parameter the strategy does not have as changed at
every step — which inflates a drift statistic silently and plausibly.

📓 First reading, 2026-09-21: neither strategy's in-sample optimisation predicts its own
out-of-sample result. `Strategy 1.19.29` gives rho +0.076 (95 % over cells: -0.034 to +0.193);
`Strategy 4.33.46` gives **-0.505 (-0.683 to -0.339)**, negative in 28 of 30 cells and on all four
metrics read. The optimiser re-decides **70-78 % of the parameters at every step**.

🔬 **SQX rellena a la apertura de la barra, en la entrada y en la salida** (XAUUSD M30,
2026-09-22). Reconstruyendo el P/L desde las barras y comparando con el que SQX reportó, las
cuatro convenciones dan: `open-open` **1.0000**, `close-open` 0.9629, `open-close` 0.9512,
`close-close` 0.8651. Y el 100 % de los `Open price` coincide con el `Open` de su barra y el 100 %
de los `Close price` con el `Open` de la barra de salida. Quien reconstruya precios desde barras
y use el cierre se equivoca en un 4-13 % de correlación, que es suficiente para mover un p y no
para que salte nada. `nulls/calibrate.convention()` lo mide por estrategia en vez de suponerlo.

🔬 **El repertorio de salidas del corpus XAUUSD son tres tipos y ninguno es un stop.**
`Exit After X Bars` 75.04 %, `Exit Signal` 19.55 %, `End Of Friday (Time)` 5.41 %; 100 % de los
trades son `Buy`. **No hay SL ni TP**, lo que elimina la ambigüedad intrabar de cualquier
reconstrucción. 95 de 757 estrategias no usan `Exit Signal` en absoluto — su salida es 100 %
independiente del camino — y 352 lo usan en menos del 10 % de sus trades. ⚠️ Es una propiedad de
**estos templates**, no del mundo: en cuanto una estrategia lleve barreras hay que calibrar la
convención intrabar antes de leer nada.

## Los bloques de un export `data=all` NO son contiguos (2026-09-23)

`orderstocsv data=all` escribe el test principal y cada crosscheck en el mismo CSV. El docstring
decía "bloques contiguos que separa la columna Symbol"; **las dos mitades de esa frase son falsas**
para un retest cross-timeframe.

- 🔬 **`Symbol` no separa nada**: los tres bloques de un crossTF son el mismo instrumento.
- 🔬 **Y no son contiguos.** El CSV sale **ordenado por fecha de apertura, con los bloques
  entrelazados**. El separador que había —bloque nuevo donde el ticket deja de crecer— partió una
  estrategia en **173 trozos**, y `tradestore.block(packed, s, 0)` devolvía una astilla del test
  principal sin que fallara nada. Con 9 estrategias salían 396 "bloques" en vez de 27.
- 🔬 **El invariante que sí vale**: cada bloque numera sus tickets desde 1 sin huecos, así que la
  **k-ésima aparición de un ticket pertenece al k-ésimo bloque** — `groupby("Ticket").cumcount()`.
  Comprobado en las 9 estrategias del proyecto `TestXAU_crossTF`: 3 bloques cada una, `max(ticket)
  == n` en las 27, y tamaños decrecientes con el timeframe (347 M30 · 180 H1 · 40 H4).
- `tradestore.pack()` devuelve ahora `torn_blocks`: las estrategias cuyos bloques no salieron como
  series completas. Una lista no vacía significa que los bloques son conjeturas.

## `export_metrics` sólo sabía leer el maestro (2026-09-24)

🔬 `sqx.export.export_metrics` fijaba `MASTER` como install, así que un databank de un proyecto del
custodio devolvía **0 filas sin error** — el `worker saw 0 strategies` es toda la señal que daba.
Ahora lleva `--role`, como `export_retest`, `export_trades` y `gate.harvest`.

- 🔬 Y un segundo modo de devolver 0 con éxito: exportar un databank cuyas `.sqx` están **sólo en
  memoria**. Un `synctofiles` no se puede pedir por HTTP si el databank lleva espacios en el nombre
  (la API corta el comando en el primer espacio, `knowhow/02-databanks.md`), así que la vía fiable
  para `Retest Markets - Family` y compañía es **parar el install**: la sincronización de cierre las
  escribe.

## `sync_bars` llevaba roto desde un refactor (2026-09-24)

🔬 `wanted()` leía `markets.FILE`, que desapareció cuando `strategies/crossmarket/inputs/markets.py`
pasó a delegar en `core.assets`. `python3 -m sqx.export.sync_bars --check` moría con
`AttributeError`. Ahora la lista sale de `assetdata.symbols()` + `markets(symbol)`.

- 📓 Con eso, el 2026-09-24 la librería declaraba **13 feeds por traer** (~110 M barras M1): los diez
  pares de the5ers, más XAGUSD, XAUUSD y Brent que han crecido en SQX. USDJPY se trajo solo:
  8.734.300 barras M1, 2003-05-05 → 2026-09-22, **139 MB** en Parquet.


## 🔬 What the trade export says about exits, and what the M1 library looks like (2026-09-24)

Measured while building `strategies/entryQuality/` and `strategies/profitShape/`.

**`Close type` is the exit reason, and it is usable.** Over the 960,705 trades of
`XAUUSD/MC_Trades` (236 strategies) it takes exactly three values: `Exit After X Bars` (720,874),
`Exit Signal` (187,853) and `End Of Friday (Time)` (51,978). **No SL and no TP anywhere.** That
confirms from the export side what `strategies/CLAUDE.md` says about the generated population, and
it is what makes a delay analysis that holds the exits fixed legitimate on this corpus — and what
will make it illegitimate the day a population carries stops.

**The M1 library is fast and clean enough to be read whole.** `XAUUSD_DukasM1_Infinox` holds
**7,949,285 bars** (2003-05-05 to 2026-09-22) and `core.barstore.source` loads all of them in
**0.4 s**. Of those bars:

- **0** are OHLC-inconsistent (`H < max(O,C)`, `L > min(O,C)`, `H < L`);
- **40,097 (0.50 %)** are flat, `High == Low`.

So the OHLC-consistency check the data-quality work would start with finds nothing here, and the
open question is the flat bars and their distribution by hour — `docs/encargos/17-calidad-del-feed.md`.
There is no need for memory-mapping or chunked reads at this size.
