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
`strategies/crossmarket/metrics.py` does.

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
Brent have no file at all. `strategies/crossmarket/pricing.point_value()` does it.

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
