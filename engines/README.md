# engines — how things are computed, shared by the studies

A study asks a question and ends in a verdict; an engine only computes. Every study imports
engines and never another study — that is the rule this folder exists to keep.

| folder | what it computes | read by |
|---|---|---|
| `market/` | A trade priced from bars the way SQX priced it: ATR, point value, cost, fill convention; and in `market/feed/`, whether the bars themselves are sound | the null engine, cross-market, entry quality, feed quality |
| `nulls/` | Random traders with the same opportunity set: the ladder on its own bars, and placement on other markets. `nulls.seed` is `null` by default — `inputs.config()` draws a fresh root from OS entropy every run (owner, 2026-09-29); an explicit int — `--seed <int>` on `monkey.report` and `gate.report`, `--set nulls.seed=<int>`, or `config.yaml` — reproduces one run. Every caller records the root it drew (`knowhow/eng/nulls-seed-fresh-per-run.md`). `nulls/windowed.py` — the gate's window-bound, cost-charged monkey | monkey, gate, crossTF, entry quality, cross-market |
| `resample/` | Reorderings and resamplings of a trade sequence | Monte Carlo, the cross-market portfolio |
| `regimes/` | The volatility state a trade was opened into | Monte Carlo |
| `inference/` | Correcting for the search: Benjamini-Hochberg, the excess over chance, SPA and StepM | the gate, the population readings, the snooping screen |
| `weekly/` | Trades into weeks × units of excess, gross and net, each trade whole in the week it closes in; the shared-sign weekly flip null, its p-values and a bulk Spearman | the WFC, the CSCV, market surfaces, the WFM |
| `variants/` | A retested variant batch read back: usable points, the in-sample / out-of-sample boundary, the per-period panel, the filters, duplicates by fingerprint, the excess over drift | the WFC, the CSCV, the WFM |

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |

Nothing here says whether a strategy is good. What a number means is the study's job.
