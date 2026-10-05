# construct/weights — how much of each member

MODELLING (PLAN §3, §5.4). A method is chosen and estimated on `build` only and its weights are
then **fixed for good: never rebalanced** (Council 2026-10-04, `DECISIONS.md` #5). Equal weight is
the one the search and the verdict use and the baseline. The other three (M8, the ones PLAN §5.4
names and AlphaForge had) are candidates: `../wf.py` compares each against equal weight out of
sample, and none may be selected by `weights.method` until the owner says so (`inputs/config.load`
refuses). Carver's handcrafting, also named by the plan, is **not built**: its grouping thresholds
and diversification multiplier are nobody's decision yet.

**Imports from:** nothing of the engine · **Consumed by:** `../search/objective.py`, `../segment.py`, `../wf.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | `REGISTRY` {name: method}; `matrix` — every combination's weights by `weights.method` as one [P, N] array | imported | build daily frame, membership → weights |
| `equal.py` | 1/K to every member | imported | a combination's build daily frame → {member: weight} |
| `risk_parity.py` | 1 / daily volatility, normalised (AlphaForge's «risk parity») | imported | same |
| `min_variance.py` | Long-only minimum variance (SLSQP) on a Ledoit-Wolf covariance shrunk towards a scaled identity; `shrunk`, `solve` | imported | same |
| `hrp.py` | Hierarchical risk parity: Ward tree on the correlation distance, recursive bisection by cluster variance; each weight written at its member's own column (AlphaForge's bug) | imported | same |

A method is `fn(build_daily: DataFrame, cfg: dict) -> {column label: weight}`: non-negative, summing
to 1, one entry per column given (`tests/test_portfolio_weights.py` checks every registry entry).

| method | holds fixed | estimates |
|---|---|---|
| `equal` | everything: 1/K whatever the data | nothing |
| `risk_parity` | every correlation at 0 | K volatilities |
| `min_variance` | the means (ignored), the shrinkage target (a scaled identity) | the K×K covariance and its shrinkage intensity |
| `hrp` | the linkage (Ward) and the split in halves | the K×K covariance, unshrunk, never inverted |

## Traps
- **No method substitutes another.** A member that does not vary on the estimation days, or an optimiser
  that does not converge, raises `ValueError` (AlphaForge fell back to risk parity in silence); the
  walk-forward reports that method as not estimable and carries on with the rest.
- **«Risk parity» here is 1/σ**, AlphaForge's definition, not equal risk contribution; the two agree
  only when the members are uncorrelated.
- **`tests/test_portfolio_segments.py` greps this folder** for the names of the later segments: a
  method reads the frame it is given and never knows which days they are.
- **What a weight multiplies is the fixed-risk P&L**, not SQX's own sizing: `real.py` scales every
  member to one unit of risk before the search (owner, 2026-09-30: fixed risk «for funded and for
  everything»). Equal weight is therefore equal risk per trade, not equal capital.
- **`matrix` calls the method once per combination** with that combination's slice of the frame:
  free for `equal`, a cost to measure for a method that estimates (a GA scores 30,000).
