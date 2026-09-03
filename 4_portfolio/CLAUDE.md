# 4_portfolio — combining strategies

Two destinations with different constraints: `funded/` for prop-firm accounts, `real/` for the
owner's own capital. `common/` holds what both need.

The design is not settled. `DECISIONS.md` is where the open questions live; add to it rather than
inventing an answer. What is agreed so far:

- Correlation is measured between **equity curves**, not between metrics.
- A portfolio's drawdown is computed on the aggregated curve, never summed from the parts.
- Strategies enter the pool only after `2_tasks/` and `3_strategies/` have passed them.

A funded account's rules (daily loss cap, total drawdown, minimum days) are constraints on the
portfolio, not filters applied afterwards. When that work starts, they get written down here first.
