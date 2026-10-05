# construct/inputs — what a run is run on

Configuration only: the knobs, the declared pool and its prohibitions, one archived strategy as
the engine reads it, and the portfolio calendar. Nothing here is computed from equity.

**Imports from:** `core.*`, `ledger.thresholds`, `engines.market.calibrate`, `sqx.inspect.feeds` (read-only) · **Consumed by:** every other layer

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.py` | Loads `config.yaml`, fills the ledger's thresholds, applies overrides, names the relaxed ones and a pseudo oos2 | imported | overrides → cfg |
| `pool.py` | A declared pool: write it once (frozen), read it, drop a firm's prohibitions (`prohibitions/<firm>.csv`; a row with an empty `plan` counts for every plan, otherwise for the plans whose key starts with it; only with `--firm`, never by default), hash what is left; `scoped`/`declared`/`prohibited_lines` are how every command carries `--firm` into the config, reads the pool and names who was dropped; the `declare` command (no `near` flag: that stays a call to `declare()`) | `python3 -m portfolio.common.construct.inputs.pool declare <name> --added-by <who> (--identity <id>[@<version>] … \| --file <ids.txt>) [--note …]` | archive → `pools/<name>.csv` → members, hash |
| `source.py` | One archived strategy as the engine reads it: trades, SQX's curve, feed, timeframe, clock, point value (fitted on same-day trades: no swap), step | imported | archive folder → dict |
| `risk.py` | A funded member's fixed-risk sizing: the step-24 stop X read from its grafted `ATRBasedValue`, SQX's `ATRRiskBasedSizingFixedRisk` amount and ATR multiple, its smallest lot, the factor that turns SQX dollars into P&L per unit of r·S; refuses a strategy without that stop | imported | archive → dict |
| `calendar.py` | The portfolio's segments: one calendar cut at the latest segment end among members (owner, Q1), the days each member borrows from its own other segment, and `pseudo`, a test run's calendar with oos1's tail renamed oos2 (`calendar.pseudo_oos2_from`) | imported | symbols → segments |

## Traps
- **Development = archived with `step` < 26** (owner, Q13): never a hand-set flag.
- **A declared pool is frozen**: a new pool is a new name, so a run can never be re-pointed at a
  universe chosen after looking.
