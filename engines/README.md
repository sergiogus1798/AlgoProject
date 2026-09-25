# engines — how things are computed, shared by the studies

A study asks a question and ends in a verdict; an engine only computes. Every study imports
engines and never another study — that is the rule this folder exists to keep.

| folder | what it computes | read by |
|---|---|---|
| `market/` | A trade priced from bars the way SQX priced it: ATR, point value, cost, fill convention | the null engine, cross-market, entry quality |
| `nulls/` | Random traders with the same opportunity set: the ladder on its own bars, and placement on other markets | monkey, gate, crossTF, entry quality, cross-market |
| `resample/` | Reorderings and resamplings of a trade sequence | Monte Carlo, the cross-market portfolio |
| `regimes/` | The volatility state a trade was opened into | Monte Carlo |
| `inference/` | Correcting for the search: Benjamini-Hochberg, the excess over chance | the gate, the population readings |

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |

Nothing here says whether a strategy is good. What a number means is the study's job.
