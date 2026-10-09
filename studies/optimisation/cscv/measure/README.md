# cscv/measure — the numbers, and nothing that judges them

| file | what it does | in → out |
|---|---|---|
| `cscv.py` | Block sums, the 6,435 halves and their complements, the best Sharpe inside scored outside, the histogram of every variant's Sharpe outside | panel → one record per partition |
| `outputs.py` | PBO, degradation line, probability of loss, haircut, dominance, selection frequency, the mother's reading | records → numbers |
| `null.py` | The equalised panel, one stationary-bootstrap draw of it (planted or not) and its CSCV | shared panel, seed, draw → summary |
| `queue.py` | The one work queue over mothers × kinds × chunks of draws, through `core.fanout` | panels, cfg → records, draws, perf |

**No row is ever concatenated.** A partition's Sharpe comes from the sums of its blocks (count,
sum, sum of squares); the complement comes from the totals. A redrawn panel's block sums are a
counts matrix (blocks × weeks) times the standardised panel, so a draw never builds its panel.

**Every draw seeds its own stream**: `SeedSequence(seed, spawn_key=(kind, draw))`. The result is
the same for any number of processes, any chunking and any set of mothers in the queue.

**Must never hold**: a threshold, a state, a word the owner reads.

