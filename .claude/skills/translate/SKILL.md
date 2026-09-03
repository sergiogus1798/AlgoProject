---
name: translate
description: Turn a .sqx strategy into readable pseudocode and an executable Python backtest, reconciled against the trades SQX exported. Use when the owner asks to translate, port, or explain a strategy in Python.
---

# /translate

Three artefacts, in this order. Stopping early is not delivering.

## 1. Pseudocode

Read the strategy's inner XML with `core/sqxfile.py` — the rules, blocks, parameters and orders. Write
plain, numbered pseudocode: entry conditions, exit conditions, filters, sizing, and every parameter
with its value. Name what the strategy does **not** have as well: no stop, no target and no trailing
is a real and easily missed property.

## 2. Python

Under `3_strategies/translate/`, following `CODESTYLE.md`. It reads bars from the data root and emits
a trade list in the same shape as SQX's `orderstocsv` export: open time, open price, size, close time,
close price, profit, MAE, MFE.

## 3. Reconciliation — the part that makes it real

Compare your trade list against the CSV SQX exported for the same strategy and window. Report:

- how many trades each produced, and how many matched on entry bar;
- the distribution of price and profit differences on matched trades;
- every unmatched trade, with the bar it should have fired on.

Then say plainly whether the translation is faithful. **An unreconciled translation is a hypothesis**,
and presenting one as a working strategy poisons every analysis built on it.

Known sources of legitimate difference: spread is inside SQX's fill prices, commission is $8 per lot
per side on this install, and overnight trades carry swap. MAE and MFE come from the M1 path inside
each trade, so bar-level data cannot reproduce them exactly — say so rather than tuning until they
match.
