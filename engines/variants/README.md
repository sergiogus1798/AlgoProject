# engines/variants — a retested variant batch, read back

What the studies of one mother's parameter cloud all read the same way: which points are usable,
where the in-sample / out-of-sample boundary is, and the per-period panel of their equity.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `panel.py` | The four admitted compositions of the split (`COMPOSITIONS`, the two named `SHORTCUTS`, `composition`, `columns`), the usable points, the N × T panel (trading days for the CSCV, weekly or monthly on request), the real boundary read off `equity.json`, and the two windows | imported | `metrics.parquet` + `equity.parquet` → points, panel, windows |
| `look.py` | What a read spends: the batch's asset and timeframe off `segments.parquet`, the ledger's door on every segment before anything opens, the compositions the door offers, and one ledger row per segment read | imported | batch + family → door, rows |
| `config.yaml` | The trade floor and the named composition, shared by the WFC and the CSCV | edited, or `--set` through either study | — |

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
