# 3_strategies — one strategy, in depth

For strategies that already survived the population filters. Smaller data, harder questions.

`extract/` pulls one strategy's full record: metrics, every trade, every walk-forward run.
`translate/` turns a `.sqx` into readable pseudocode and an executable Python backtest.
`analysis/` does the per-strategy maths: MAE/MFE, stop studies, parameter sensitivity, regimes.

## Translation is not done until it reconciles

A translation ships with three artefacts: the pseudocode, the Python, and a **reconciliation report**
comparing the Python's trades against the CSV SQX exported for the same strategy and window. Report
the differences; do not bury them. An unreconciled translation is a hypothesis, and saying otherwise
is the single easiest way to poison everything downstream.

## Traps

- **MAE and MFE are in account currency, not points**, and each trade has its own size. Convert per
  trade: `price = abs(MAE_$) / (Size * pointValue)`.
- **Drop the last row when its close price is blank** — it is an unfilled pending order.
- **Never present a stop simulation without a slippage sensitivity.** The tighter the stop, the more
  of the answer is the fill assumption. See `knowhow/07-practices.md`.
- The generated XAUUSD strategies carry **no stop, no target and no trailing** — check what a
  strategy actually does before assuming the builder's settings reached it.
