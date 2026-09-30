# construct/inputs — what a run is run on

Configuration only: the knobs, the declared pool and its prohibitions, one archived strategy as
the engine reads it, and the portfolio calendar. Nothing here is computed from equity.

**Imports from:** `core.*`, `ledger.thresholds`, `engines.market.calibrate`, `sqx.inspect.feeds` (read-only) · **Consumed by:** every other layer

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.py` | Loads `config.yaml`, fills the ledger's thresholds, applies overrides, names the relaxed ones | imported | overrides → cfg |
| `pool.py` | A declared pool: write it once (frozen), read it, drop a firm's prohibitions, hash what is left | imported | `pools/<name>.csv` → members, hash |
| `source.py` | One archived strategy as the engine reads it: trades, SQX's curve, feed, clock, point value, step | imported | archive folder → dict |
| `risk.py` | A funded member's fixed-risk sizing: the step-24 stop X read from its grafted `ATRBasedValue`, SQX's `ATRRiskBasedSizingFixedRisk` amount and ATR multiple, its smallest lot, the factor that turns SQX dollars into P&L per unit of r·S; refuses a strategy without that stop | imported | archive → dict |
| `calendar.py` | The portfolio's segments: one calendar cut at the latest segment end among members (owner, Q1), and the days each member borrows from its own other segment | imported | symbols → segments |

## Traps
- **Development = archived with `step` < 26** (owner, Q13): never a hand-set flag.
- **A declared pool is frozen**: a new pool is a new name, so a run can never be re-pointed at a
  universe chosen after looking.
