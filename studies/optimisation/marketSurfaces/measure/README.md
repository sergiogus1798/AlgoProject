# marketSurfaces/measure — what are the numbers?

| file | what it does | in → out |
|---|---|---|
| `order.py` | The order of the variants on the main market against another market's: ties, and the weighted mean. | per-market values → joint |
| `power.py` | The planted transmission: a no-edge draw of a market with the main market's order mixed in. | draws → power |
| `premium.py` | The top-20 % premium: what picking by the main market buys on another one, in units of its spread. | net excess → premium |
| `reading.py` | One reading across markets: each market's rho and premium, the joint ones, their null and the power. | panels → numbers |

Must never hold a threshold that judges; that is `verdict/`. The cuts used here (`min_common`,
`max_ties`) say which markets enter a mean, not what the mean is worth.

**One sign vector per draw, for every market.** `reading.measure` draws the signs once and applies
them to each market's gross and net panels; the main market's vector goes into `flip.spearman` as
the fixed side. `tests/test_marketsurfaces.py` checks both.

**The null of a market is drawn on its common set**, the same variants as its observed rho.
