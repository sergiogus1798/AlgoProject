# marketSurfaces/measure — what are the numbers?

| file | what it does | in → out |
|---|---|---|
| `order.py` | The share of tied variants, the weight of each market (1, or 1 shared by a group), and the weighted joint mean, NaN-aware, of one row or of every draw | per-market values → joint |
| `premium.py` | The main market's top by net excess, and a market's premium: (median of the top − median of all) / IQR, of one row or of every draw | net excess → premium |
| `power.py` | Normal scores, the planted transmission (a no-edge draw mixed with the main market's order to an exact Spearman) and the share of planted draws read positive | draws → power |
| `reading.py` | One whole reading: per market rho, tails, ties, premium and the mother's place; the joint order and premium with their nulls; the same per category; the power curve | panels → numbers |

Must never hold a threshold that judges; that is `verdict/`. The cuts used here (`min_common`,
`max_ties`) say which markets enter a mean, not what the mean is worth.

**One sign vector per draw, for every market.** `reading.measure` draws the signs once and applies
them to each market's gross and net panels; the main market's vector goes into `flip.spearman` as
the fixed side. `tests/test_marketsurfaces.py` checks both.

**The null of a market is drawn on its common set**, the same variants as its observed rho.
