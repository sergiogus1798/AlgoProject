# strategies — one strategy, in depth

For strategies that already survived the population filters. Smaller data, harder questions.

`extract/` pulls one strategy's full record: metrics, every trade, every walk-forward run.
`translate/` turns a `.sqx` into readable pseudocode and an executable Python backtest.

## One study, one folder

Everything else here is a **study folder**, holding its own maths, its own command, its own
configuration and its own open questions:

| folder | the question it answers |
|---|---|
| `crossmarket/` | does the edge transfer to markets the strategy never saw, or is it just being long? |
| `monteCarlo/` | how much of the result is luck, and of what kind: order, composition, execution or regime? |

This is not the `analysis/` + `reports/` split that `tasks/` uses, and the difference is deliberate.
A population study is one pipeline with many renderings; a strategy study is one question with its
own statistics, its own configuration and its own traps, and there will be many of them — stops,
MAE/MFE, parameter sensitivity, regimes, exposure-adjusted return. Keeping each one whole means the
argument for its design sits next to the code that implements it, and a study can be read, changed or
retired without touching the others.

What is genuinely shared goes outside: `core/trades.py` and `core/bars.py` read the export formats,
`sqx/export/` produces them, `sqx/curate/` acts on a verdict inside SQX. A helper only two studies
need is not shared yet — copy it, and move it to `core/` when a third one wants it.

Every study folder carries a `README.md` with the one-row-per-file table, and a
`POSSIBLE_IMPROVEMENTS.md` when its design had real alternatives. `crossmarket/` has one, and its
first section is the important one: **how a null models the real trades is open by design**, there is
no single correct randomisation, and the choice moves the answer. Argue it there, in writing, before
changing it in code.

## Translation is not done until it reconciles

A translation ships with three artefacts: the pseudocode, the Python, and a **reconciliation report**
comparing the Python's trades against the CSV SQX exported for the same strategy and window. Report
the differences; do not bury them. An unreconciled translation is a hypothesis, and saying otherwise
is the single easiest way to poison everything downstream.

The same rule now has teeth elsewhere: `crossmarket/pricing.reconcile()` re-derives the fill
convention per market and the study refuses to interpret a market it could not reproduce. Measured
on XAUUSD H1 the convention is **open-to-open with a median price error of exactly 0.0**.

## Traps

- **MAE and MFE are in account currency, not points**, and each trade has its own size. Convert per
  trade: `price = abs(MAE_$) / (Size * pointValue)`.
- **Drop the last row when its close price is blank** — it is an unfilled pending order.
- **Never present a stop simulation without a slippage sensitivity.** The tighter the stop, the more
  of the answer is the fill assumption. See `knowhow/07-practices.md`.
- The generated XAUUSD strategies carry **no stop, no target and no trailing** — check what a
  strategy actually does before assuming the builder's settings reached it.
- **1.2% of XAUUSD entries do not land on a bar open**, and on other projects it is far more. Those
  are pending orders filled inside a bar: a price-conditional selection that any study placing
  synthetic trades has to measure before trusting its comparison.
