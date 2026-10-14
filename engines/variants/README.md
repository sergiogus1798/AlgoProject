# engines/variants — a retested variant batch, read back

What the studies of one mother's parameter cloud all read the same way: which points are usable,
where the in-sample / out-of-sample boundary is, and the per-period panel of their equity.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | A retested variant batch read back, shared by the studies that read one. | — | — |
| `excess.py` | A batch's trades net of the market's drift: per trade, per variant and year, and per day. | imported | trades of one leg + bars + costs → excess per trade, per variant and year, per variant and day |
| `filters.py` | Which variants of a batch enter a composition: no controls, no exact duplicates, two trade floors. | imported | `metrics.parquet` + `values` → surviving rows + counts |
| `fingerprint.py` | Exact duplicates among a batch's variants, told by the trades they made and not by a total. | imported | trades → one hash per variant → variants kept, duplicate share |
| `look.py` | What reading a variant batch spends: its study, the door on each segment, and the ledger rows. | imported | batch + family → door, rows |
| `panel.py` | A retested variant batch read back: its C3 columns by split, its usable points, its panel. | imported | `metrics.parquet` + `equity.parquet` → points, panel, windows |
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
