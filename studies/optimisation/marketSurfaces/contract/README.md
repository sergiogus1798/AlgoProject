# marketSurfaces/contract — how is it read?

| file | what it does | in → out |
|---|---|---|
| `tabs.py` | The four tabs: the reading (table and rho bars), the two 10 × 10 matrices, one surface per market with the mother marked, and the checks | numbers → tabs |
| `grids.py` | Two more: «rejillas», a `grid` per market, segment and ordered pair of parameters with θ₀ as `mark` and one `scale_range` per pair and segment; and «consenso», per cell the number of markets whose top decile holds it (`levels` 0..N) | cells + parameters → tabs |

Must never judge. `grids.py` is the one place that shapes numbers — the median per cell and the
top-decile count are what a grid *is*, not a measurement a verdict reads; nothing in `verdict/`
depends on them. The mother is left out of every cell's median and kept on the axes: her own score
in her own cell would vouch for itself. Every text is Spanish and the costs caveat (`COSTS`) opens the first tab
and closes the verdict, because every number here was produced at SQX's factory costs.
