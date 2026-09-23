# walkForwardCorrelation/measure — the numbers

| file | what it does | in → out |
|---|---|---|
| `correlation.py` | Which points are usable, Spearman's rho, its 95 % interval, and the call | C3 → rho, call |
| `rules.py` | The three ways a person picks one parameter set off a surface, behind one signature | scores, grid → a choice |
| `cscv.py` | The partitions, the per-period score, and the choose-then-score loop | panel → one row per partition |

**The interval is the point, not the coefficient.** With a dozen tuples the sampling error on a
correlation is enormous, so `correlation.verdict` answers `indeciso` rather than pretend.

**The score is pluggable and the plug is narrow.** `SCORES` holds `sharpe` and `sortino`, both
rates per period, and `run` uses whichever it is given on *both* halves of every partition. Ret/DD
is deliberately absent: it grows with elapsed time, so it cannot compare windows of different
lengths. The deflated Sharpe in `../verdict/trials.py` stays a Sharpe regardless — ranking picks
the variant, the DSR judges it.

**Every rule has the same signature — `(score, grid, rng) → position`** — because the study's whole
subject is the difference between rules. A rule that needed its own call site could not be compared
against the others, and the grid arrives in the panel's column order: a rule answers with a
position, so a grid ordered differently would silently name a different variant.

`cscv.carry` fits the out-of-sample Sharpe on the in-sample one across **every** variant of a
partition, never on the chosen one. Regressing the winner alone measures a seesaw — the two halves
are complementary — and reads *more* negative where the edge is real. See
`../POSSIBLE_IMPROVEMENTS.md`.
