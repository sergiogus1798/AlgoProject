# sqx/variants/design — which 5,000 combinations, and why those

Pure maths. Nothing here opens a `.sqx` or writes a byte; it turns contract C1 into a table of
tuples. That is what makes the design arguable on its own: the grid can be changed and inspected
without fabricating anything, with `make.py --design-only`.

| file | what it does | in → out |
|---|---|---|
| `levels.py` | The values each parameter may take: the brief's own for the live ones, a rebuilt range for the frozen ones | brief → levels |
| `strata.py` | The three ways a tuple gets into the design, behind one signature | levels, budget → tuples |
| `canaries.py` | The controls: the origin, the known-result canaries, the inert pairs | brief, known results → rows |
| `plan.py` | Puts it together and assigns the identifiers | brief → the plan |

## The strata

Every one takes `(levels, budget, context)` and returns tuples, and they are collected in
`strata.STRATA`. Adding a fourth is a function and a row here.

| stratum | share | what it varies | what it holds fixed | what it is for |
|---|---|---|---|---|
| `neighbourhood` | 20 % | live parameters, ±`radius` level steps around the plateau centre | the frozen ones, at their value | how steep the surface is exactly where the strategy would be deployed. Nothing else resolves distance 1 |
| `factorial` | 60 % | live parameters, on a coarsened grid | the frozen ones | interactions. A **complete** grid over fewer levels, because a sampled grid cannot show that two parameters matter together |
| `coverage` | 20 % | **every** parameter, frozen ones included | nothing | the corners the other two never visit, and a test of the freezing decision rather than a restatement of it |

The shares are read from the brief, not from `config.yaml`: they are a property of the strategy
being studied, and `strategies/sppUltra` sets them.

## The three decisions worth arguing with

**The coarse factorial saturates rather than being fixed.** Each parameter starts at
`min_levels` and the grid grows one parameter at a time — most variance explained first — for as
long as the product still fits the budget. A flat "three levels each" spends the same budget
resolving a parameter that barely moves the result as one that decides it. When even the minimum
product overruns the budget the grid is sampled and stops being complete; that is reported.

**The frozen parameters get a range nobody gave them.** The brief freezes a parameter on the
duplicate test — proof that it never moved a backtest — and hands over a value, not a span. The
coverage stratum has to vary it anyway or it is only restating the brief's own conclusion. The range
is rebuilt the way SQX builds its own permutation ranges, which is measured in
`knowhow/sqx-format/declared-parameters.md`: ±30 % of the value stepped and rounded, and a flat 0..6 for a shift,
because a percentage of a small integer collapses to a handful of distinct values. **This is an
assumption, and it is the one to revisit first** if a coverage row ever disagrees with the freezing.

**`n_target` is a cap.** The controls go in first and count against it, then each stratum takes its
share of what is left and hands any shortfall to the next. Tuples are deduplicated across strata and
controls alike, first producer keeps it, and nothing is ever repeated to reach a round number. Two
identical `.sqx` in one databank are one strategy once SQX is done with them, so a duplicate is not
a wasted slot — it is a manifest row with no file behind it.
