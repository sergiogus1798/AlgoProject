# cscv/measure — the numbers, and nothing that judges them

| file | what it does | in → out |
|---|---|---|
| `cscv.py` | Combinatorially symmetric cross-validation off block sums: each half of the blocks chooses, the other judges. | panel → one record per partition |
| `null.py` | The panel with nothing to choose: every column at one Sharpe, its weeks redrawn with replacement. | shared panel, seed, draw → summary |
| `outputs.py` | What the partitions of one CSCV say: the paper's four outputs, the haircut and who gets chosen. | records → numbers |
| `queue.py` | One queue for every CSCV of a run: mothers x (real, null on net and on gross, each planted Sharpe) x draws. | panels, cfg → records, draws, perf |

**No row is ever concatenated.** A partition's Sharpe comes from the sums of its blocks (count,
sum, sum of squares); the complement comes from the totals. A redrawn panel's block sums are a
counts matrix (blocks × weeks) times the standardised panel, so a draw never builds its panel.

**Every draw seeds its own stream**: `SeedSequence(seed, spawn_key=(kind, draw))`. The result is
the same for any number of processes, any chunking and any set of mothers in the queue.

**Must never hold**: a threshold, a state, a word the owner reads.

