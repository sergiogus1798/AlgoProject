# wfc/measure — the numbers

| file | what it does | in → out |
|---|---|---|
| `correlation.py` | Spearman's rho, its 95 % interval, and the call; which points are usable is `engines/variants/panel.points` | C3 → rho, call |
| `persistence.py` | The criteria metrics (owner, 2026-10-04: computed and shown, no threshold): the share of the build's top that stays in the top of an out-of-sample window, read as its excess over `keep`, its value by chance; the median over variants of Sharpe OOS/IS above the in-sample floor; and both under a zero-edge null that flips the sign of each out-of-sample day for every variant at once, so the variants keep their dependence | per-variant vectors + daily profit → share, excess, ratio, null percentiles |

**The interval is the point, not the coefficient.** With a dozen tuples the sampling error on a
correlation is enormous, so `correlation.verdict` answers `indeciso` rather than pretend.
