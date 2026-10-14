# construct/inputs — what a run is run on

Configuration only: the knobs, the declared pool and its prohibitions, one archived strategy as
the engine reads it, and the portfolio calendar. Nothing here is computed from equity.

**Imports from:** `core.*`, `ledger.thresholds`, `engines.market.calibrate`, `sqx.inspect.feeds` (read-only) · **Consumed by:** every other layer

| file | what it does | run it | in → out |
|---|---|---|---|
| `backfill.py` | One-off: fill `clock` and `commission` into the manifests archived before they were frozen there. | `python3 -m portfolio.common.construct.inputs.backfill [--yes]` | archive → table, manifests |
| `calendar.py` | The portfolio's one calendar (owner, Q1), and what a member borrows from its own other segments. | imported | symbols → segments |
| `config.py` | The engine's knobs: config.yaml with the ledger's thresholds filled and any override applied. | imported | overrides → cfg |
| `pool.py` | A declared pool of archived strategies: write it once (frozen), read it, drop prohibitions, hash it. | `python3 -m portfolio.common.construct.inputs.pool declare <name> --added-by <who> (--identity <id>[@<version>] … \| --file <ids.txt>) [--note …]` | archive → `pools/<name>.csv` → members, hash |
| `risk.py` | A member's fixed-risk factor: the step-24 ATR stop's X, the sizing it scales, its floor lot. | imported | archive → dict |
| `source.py` | One archived strategy as the engine reads it — files only, nothing recomputed. | imported | archive folder → dict |

## Traps
- **Development = archived with `step` < 26** (owner, Q13): never a hand-set flag.
- **A declared pool is frozen**: a new pool is a new name, so a run can never be re-pointed at a
  universe chosen after looking.
