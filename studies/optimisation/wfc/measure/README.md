# wfc/measure — the numbers

| file | what it does | in → out |
|---|---|---|
| `correlation.py` | Spearman's rho, its 95 % interval, and the call; which points are usable is `engines/variants/panel.points` | C3 → rho, call |

**The interval is the point, not the coefficient.** With a dozen tuples the sampling error on a
correlation is enormous, so `correlation.verdict` answers `indeciso` rather than pretend.
