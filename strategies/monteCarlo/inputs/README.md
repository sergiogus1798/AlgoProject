# monteCarlo/inputs — what is this study being run on?

The configuration layer. It turns three outside things — `config.yaml`, the asset's cost facts and
a CSV of trades SQX exported — into the two objects every other layer takes: a `cfg` dict and a
`stream` dict of arrays. **Nothing here is computed from a simulation**, which is what makes it
safe for any layer, inference included, to import.

It is separate from `model/` because the two answer different questions: this layer says *which
numbers the study starts from*, `model/` says *what we are pretending could have happened instead*.

**Imports from:** `core/` only  ·  **Consumed by:** every other layer
**Must not contain:** a randomisation, a statistic, or a threshold

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.py` | Reads `config.yaml`, applies `--set` overrides, and scales the block sweep to the trade count | imported | overrides → config |
| `costs.py` | The asset's cost facts, the cost SQX really charged per trade, and the cross-check between them | imported | symbol + trades → USD |
| `stream.py` | **The input contract.** Any time-ordered trade list — one strategy or a portfolio — as the arrays every family runs on | imported | CSV → arrays |

## Contracts and traps

- **`stream.py` is the only contract the study has.** Every family takes a time-ordered trade list
  and nothing else. That is why a **portfolio** needs no separate code: `stream.portfolio()`
  concatenates several strategies' trades, sorts by time, and the same families run unchanged.
  `stream.overlap()` measures how often two positions were open at once; the additive equity curve
  stays valid, but the longest losing run means something different at portfolio level.
- **Costs are recovered, not modelled.** The trade export carries no cost column, so each trade's
  cost is `gross − net` (`core.trades.cost`) — commission and swap exactly as SQX booked them. The
  asset file supplies spread and point value from its `sqx_default` side, not its `use:` side: this
  study stresses a backtest SQX already ran, so the costs that belong in it are the ones charged in
  it. `costs.crosscheck()` warns when the modelled and recovered commissions diverge, and that
  warning invalidates Family C only.
- **`config.yaml` lives one level up, in the module root**, because `docs/manual/07-montecarlo.md`
  names it by that path. `config.FILE` resolves it with `parents[1]`; moving either breaks the other.
- **`HEADLINE` and `BASELINE` live here**, not in `simulate/sweeps.py`. Which sub-run the gates and
  the report speak about is a choice of the study, not a result of it — and keeping it here is what
  lets `verdict/` reach it without importing `simulate/`.
