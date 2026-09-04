# Portfolio — open decisions

Questions the owner has not settled yet. Nothing here is implemented; do not guess an answer.

| # | question | why it matters |
|---|---|---|
| 1 | Funded vs real: same strategy pool, or different admission bars? | A daily loss cap punishes variance that own capital tolerates |
| 2 | How many strategies per portfolio, and per symbol? | Decides whether correlation or capacity is the binding constraint |
| 3 | Fixed weights, volatility parity, or optimised? | Optimised weights on backtested curves overfit hard |
| 4 | What counts as too correlated, and measured over what window? | A single threshold on the whole history hides regime clustering |
| 5 | Rebalancing: never, on a schedule, or on degradation? | Changes what the backtest of the portfolio even means |
| 6 | Prop-firm rules to encode: daily loss, total drawdown, minimum days, consistency | These are constraints, not post-hoc filters |

Answer one, and it moves from here into `portfolio/CLAUDE.md` as a settled rule.
