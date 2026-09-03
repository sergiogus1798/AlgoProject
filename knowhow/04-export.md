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
`Filters result` (PASSED/FAILED) automatically. Project copies of the views live in `1_sqx/views/`.

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
still. `1_sqx/export/export_metrics.py` does exactly this.

🔬 A databank created with `-databank action=create` is **not** picked up by the startup
sync-from-files — only databanks already registered in the project are. Staging into an existing
`Results` databank works; creating `MetricsTmp` and loading into it does not.
