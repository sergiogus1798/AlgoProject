# marketSurfaces/contract — how is it read?

| file | what it does | in → out |
|---|---|---|
| `tabs.py` | The reading (table and Spearman bars), the two matrices, the checks, and `TERMS` (Jaccard, Spearman…: the tooltips of the table headers and the glossary) | numbers → tabs |
| `density.py` | «Una superficie por mercado»: per metric and segment one `distribution` with a KDE series per market (the window's toggles switch them), the mother marked on the main market | cells → tab |
| `grids.py` | Two more: «rejillas», a `grid` per market, segment, metric and ordered pair of parameters with θ₀ as `mark` and one `scale_range` per pair, segment and metric, symmetric around the metric's neutral point (`NEUTRAL`: 0, or 1 for Profit Factor) on the diverging red → green scale; and «consenso», per cell the number of markets whose top decile holds it (`levels` 0..N) | cells + parameters → tabs |
| `criteria.py` | The criteria metrics as one text table per segment of the reading tab («Métricas para criterios — sin umbral todavía»: J, J by chance, lift and its zero-edge range per market, the mother in each top) and as the summary's flat fields (`lift_Jaccard_mediano_<segment>`, `exceso_madre_en_top_<segment>`) | imported | lifts → tables, summary |

Must never judge. `grids.py` is the one place that shapes numbers — the median per cell and the
top-decile count are what a grid *is*, not a measurement a verdict reads; nothing in `verdict/`
depends on them. The mother is left out of every cell's median and kept on the axes: her own score
in her own cell would vouch for itself. Every text is Spanish and the costs caveat (`COSTS`) opens the first tab
and closes the verdict, because every number here was produced at SQX's factory costs.
