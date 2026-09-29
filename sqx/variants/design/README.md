# sqx/variants/design — which 5,000 combinations, and why those

Pure maths. Nothing here opens a `.sqx` or writes a byte; it turns contract C1 into a table of
tuples. That is what makes the design arguable on its own: the grid can be changed and inspected
without fabricating anything, with `make.py --design-only`.

| file | what it does | in → out |
|---|---|---|
| `levels.py` | The values each parameter may take: the brief's own for the live ones, a rebuilt range for the frozen ones | brief → levels |
| `strata.py` | The three ways a tuple gets into the design, behind one signature | levels, budget → tuples |
| `canaries.py` | The controls: the origin, the known-result canaries, the inert pairs | brief, known results → rows |
| `plan.py` | Puts it together and assigns the identifiers; drops a pilot's banned levels first | brief, banned levels → the plan |
| `pilot.py` | Which few hundred tuples the pilot samples (live parameters only, Sobol), and which levels its trade counts say do not trade enough (OPEN.md #41) | imported by `sqx.variants.pilot` | live levels, trade counts → banned levels |

## The pilot, before any of it (OPEN.md #41, owner 2026-09-29)

ON by default (`pilot.enabled`, `--no-pilot` to skip). Half a design's budget can go on
combinations that barely trade (🔬 2026-09-24: 1,002 of 2,000 fabricated rows under 30 trades in
sample) — a region nothing in this folder knew was silent until the whole batch had already been
fabricated, loaded and retested. The pilot answers that cheaply, before `build`'s `live()` levels
reach any stratum: `pilot.sample` draws a few hundred tuples over the live parameters (Sobol, the
frozen ones untouched — whether a region trades is decided by what moves), `sqx.variants.pilot`
fabricates and retests them on the same project the full batch will use, and `pilot.decide` reads
back which live-parameter LEVELS (never a whole parameter, and never the origin's own value) traded
below `pilot.min_trades` with enough support (`pilot.min_support`) to trust the median. `plan.build`
then removes exactly those levels before any stratum samples from them, and names them in its own
report (`pilot_dropped`) and in `pilot.json` — a batch is never smaller than what it says it is.

## The strata

Every one takes `(levels, budget, context)` and returns tuples, and they are collected in
`strata.STRATA`. Adding a fourth is a function and a row here.

| stratum | share | what it varies | what it holds fixed | what it is for |
|---|---|---|---|---|
| `neighbourhood` | 20 % | live parameters, ±`radius` level steps around the plateau centre | the frozen ones, at their value | how steep the surface is exactly where the strategy would be deployed. Nothing else resolves distance 1 |
| `factorial` | 60 % | live parameters, on a coarsened grid | the frozen ones | interactions. A **complete** grid over fewer levels, because a sampled grid cannot show that two parameters matter together |
| `coverage` | 20 % | **every** parameter, frozen ones included | nothing | the corners the other two never visit, and a test of the freezing decision rather than a restatement of it |

The shares are read from the brief, not from `config.yaml`: they are a property of the strategy
being studied, and `studies/breakage/spp` sets them.

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
because a percentage of a small integer collapses to a handful of distinct values. **Confirmed final
by the owner (OPEN.md §23, 2026-09-29):** the ±30 % span is not an open assumption to revisit — it
is deliberately the same range SQX itself uses for a permutation, so a coverage row disagreeing with
the freezing is read as a finding about the strategy, not as a prompt to widen the span.

**`n_target` is a cap.** The controls go in first and count against it, then each stratum takes its
share of what is left and hands any shortfall to the next. Tuples are deduplicated across strata and
controls alike, first producer keeps it, and nothing is ever repeated to reach a round number. Two
identical `.sqx` in one databank are one strategy once SQX is done with them, so a duplicate is not
a wasted slot — it is a manifest row with no file behind it.
