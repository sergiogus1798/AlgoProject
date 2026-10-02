# cscv/measure — the numbers

| file | what it does | in → out |
|---|---|---|
| `rules.py` | The three ways a person picks one parameter set off a surface, behind one signature | scores, grid → a choice |
| `cscv.py` | The partitions, the per-period score, the block sums each half is scored from, and the choose-then-score loop | panel → one row per partition |

**The score is pluggable and the plug is narrow.** `SCORES` holds `sharpe` and `sortino`, both
rates per period, and `run` uses whichever it is given on *both* halves of every partition. Ret/DD
is deliberately absent: it grows with elapsed time, so it cannot compare windows of different
lengths. The deflated Sharpe in `../verdict/trials.py` stays a Sharpe regardless — ranking picks
the variant, the DSR judges it.

**Every rule has the same signature — `(score, grid, rng) → position`** — because the study's whole
subject is the difference between rules. The grid arrives in the panel's column order: a rule
answers with a position, so a grid ordered differently would silently name a different variant.

`cscv.carry` fits the out-of-sample Sharpe on the in-sample one across **every** variant of a
partition, never on the chosen one. Regressing the winner alone measures a seesaw — the two halves
are complementary — and reads *more* negative where the edge is real. See
`../../wfc/POSSIBLE_IMPROVEMENTS.md`.
