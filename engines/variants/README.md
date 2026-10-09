# engines/variants — a retested variant batch, read back

What the studies of one mother's parameter cloud all read the same way: which points are usable,
where the in-sample / out-of-sample boundary is, and the per-period panel of their equity.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `panel.py` | Step 17's three compositions under their own keys (`KEYS` c1 c2 c3, `COMPOSITIONS`, `key`, `label`; `build -> oos1` alone is out), the two named `SHORTCUTS`, `composition`, `columns`, the usable points, the N × T panel (trading days for the CSCV, weekly or monthly on request), the real boundary read off `equity.json`, and the two windows | imported | `metrics.parquet` + `equity.parquet` → points, panel, windows |
| `filters.py` | Which variants a composition measures: no controls, no exact duplicates, an inside floor of `15 × k` trades and an outside floor of `10` per year (a mother under a floor warns and the floor is skipped), each filter counted; the per-variant measure comes in as `values`, never `NetProfit`; the seal is asked before oos2 is read | imported | `metrics.parquet` + `values` → surviving rows + counts |
| `look.py` | What a read spends: the batch's asset and timeframe off `segments.parquet`, the ledger's door on every segment before anything opens, the compositions the door offers, `ledger.gate.seal` on every segment, and one ledger row per segment read (`log_all`: the three compositions) | imported | batch + family → door, rows |
| `excess.py` | The excess over the market's drift, one function for steps 14, 16.5 and 17: `per_trade` (`reprice.real` minus `tradelevel.drift_term`, per trade), `per_year` (its sum per variant over one window, per year of the window) and `daily` (variants × days: each held bar books its move to the next open less an equal share of the trade's drift, the exit's day books the rest, so a row sums to the per-trade excess under every drift variant). `drift_span` picks the bars the drift is measured on | imported | trades of one leg + bars + costs → excess per trade, per variant and year, per variant and day |
| `fingerprint.py` | Exact duplicates by what was traded: `prints` hashes each variant's trade list (entry and exit time, side, lots, prices, result) and `keep` leaves one variant per fingerprint, the mother first, with the share dropped. `filters.screen(prints=...)` uses it; without it the screen still compares rounded `NetProfit` | imported | trades → one hash per variant → variants kept, duplicate share |
| `config.yaml` | The trade floor, the named composition and the `panel` floors (ledger rows `wfc.*`), shared by the WFC and the CSCV | edited, or `--set` through either study | — |

**The IS/OOS boundary is not a setting.** `split` reads it off `equity.json`, which the harvest wrote
from the harness that produced the numbers. **`usable` narrows the panel to the points the correlation
accepted**, so the rho and the PBO are two statements about one set of points — which is why the WFC
and the CSCV share this engine and this config rather than two copies of each.

**`build` is always in sample** (owner, 2026-09-27, encargo 24 Q11): in sample is `build` or
`build+oos1`, out of sample is what is left, and `oos1` may sit out entirely — four compositions,
each a choice of columns `sqx.variants.collect` already wrote, so none reruns a backtest.
`composition` refuses any other. **Every read is recorded**: `look.admit` asks `ledger.gate.allow`
for each segment before the parquet is opened, and `look.log` writes one row per segment, its note
opening `lote <batch>` so `ledger.blind` never rebuilds a look that recorded itself. The study id
needs a template family the batch does not carry, so the WFC and the CSCV take `--family`.
