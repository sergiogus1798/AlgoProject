---
q: sqx.variants.equity 17 bloques donde ninguna curva cuadra con lo que SQX guardo; equity.py reads live databank not export; running structural or atrCalculator after variants execute destroys WFC equity data
tag: 🔬  date: 2026-09-26  see: sqx-drive/variants-execute-needs-worker-it-started
---
# `sqx.variants.equity` reads the LIVE `WFC_Build/OOS1/OOS2` databank folders, not an export — running any later batch through the same project erases the previous one's equity data
`sqx.variants.execute --work <batch>` always retests into the workflow project's own three WFC
databanks (`WFC_Build`, `WFC_OOS1`, `WFC_OOS2`) — that is the whole point of "one project holds
everything" (hard rule 10). But `sqx.variants.equity` (`leg_curves()`, `harvest()`) reads
`leg["databank_dir"]` from `ran.json` and globs `*.sqx` **directly off disk in that databank
folder** — it does not read from `sqx.export.export_retest`'s parquet. Every `sqx.variants.execute`
call **clears and reloads** those same three databanks for its own batch (`Reports removed` in the
SQX log), so running a *different* batch through the same project — the structural ablation batch
(step 23) or an ATR stopgrid batch (step 24) — silently deletes the previous batch's `.sqx` files
from those databanks. The exported `trades.parquet` from `export_retest` survives (it was copied out
already), but it is not what `equity.py` reads, so it does not help.

**Consequence: `sqx.variants.equity`/`collect` must run immediately after `sqx.variants.execute`,
before anything else touches the same project's WFC databanks** — not "whenever it's convenient
later". The four-command pipeline in the `/variants` skill (`make` → `execute` → `equity` →
`collect`) is not just a suggested order, it is load-bearing: skipping straight to a different study
(structural, ATR) after `execute` and coming back later finds the well-known WFC 1/2/3 databanks
holding someone else's strategies.

## Evidence
- 2026-09-26, `USDJPY_workflow_profiling_v1`. Order of operations: `variants.execute` for mother
  `1.29.55` (1.093 variants, WFC 1/2/3 complete) → `variants.execute` for mother `1.28.59` (1.457
  variants) → `sqx.structural.make`/`execute` (12 files, reused the same three databanks) →
  `sqx.variants.stopgrid`/`execute` pass1 (2 files) → pass2 (22 files) — each overwrote
  `WFC_Build`/`WFC_OOS1`/`WFC_OOS2` again.
- Calling `sqx.variants.equity --work .../Strategy_1.29.55` afterwards: `PROGRESS 100 22 variantes x
  5081 dias unidos` — **22**, not the 1.093 this batch actually had; that 22 is the leftover count
  from the *last* thing run in that project (the ATR pass2 batch). Then:
  `17 bloques donde NINGUNA curva cuadra con lo que SQX guardo` listing every (segment, market)
  combination, with the per-block table confirming "22 curvas" everywhere it should say 1.093.
- Fix: re-run `sqx.variants.execute --work <mother>` again (regenerating that mother's WFC 1/2/3 in
  SQX — a second look at `oos2` for that mother, paid consciously) and run `equity`/`collect`
  **immediately**, before touching the project's WFC databanks with anything else, this time.
- 🤔 Untested whether there is a way to snapshot/restore a databank's `.sqx` files (a plain directory
  copy of `databanks/WFC_Build` etc. before the next `execute` clears it) so `equity.py` could be
  pointed at the snapshot instead of the live folder — would avoid re-spending `oos2` on a rerun.

## A second, real bug surfaced once the data was correct again

With the right 1.093/1.457-variant batches back in the databanks, `equity.py` **still** refused —
`sqx/variants/equity.py`'s `all_off` gate assumed "every variant of one market off" could only mean
a wrong-result read (comment: "shows up as every variant off, not a handful"). On a population this
homogeneous (1.093-1.457 variants of ONE mother, same fixed condition, same market, differing mostly
by period), it is not rare for **every** variant to share an open position on one specific
(segment, market) at the exact boundary date — measured: build/USDCAD across the first ten P-files,
diff $447-$840 against an `AvgWin` of $640-$720, i.e. one trade's worth, not a mis-read. Fixed in
`sqx/variants/equity.py`: added `PLAUSIBLE_TRADES = 3` and an `implausible` list alongside the
existing `off` list — a file only counts toward the fatal `all_off` gate when its curve/NetProfit
gap exceeds `PLAUSIBLE_TRADES × max(|MaxProfit|, |MaxLoss|)` for that file's own result, not merely
when it differs at all. Verified: re-running `equity.py` on both completed mothers (1.093 and 1.457
variants) after the fix exits 0 with zero `implausible` blocks in either, and `sqx.variants.collect`
then passes its own canary check (`all_identical: false`) on both.

