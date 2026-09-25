# engines/variants — a retested variant batch, read back

What the studies of one mother's parameter cloud all read the same way: which points are usable,
where the in-sample / out-of-sample boundary is, and the per-period panel of their equity.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `panel.py` | The two readings of the split (`MODES`, `columns`), the usable points, the N × T panel, the real boundary read off `equity.json`, and the two windows | imported | `metrics.parquet` + `equity.parquet` → points, panel, windows |
| `config.yaml` | The trade floor and the split mode, shared by the WFC and the CSCV | edited, or `--set` through either study | — |

**The IS/OOS boundary is not a setting.** `split` reads it off `equity.json`, which the harvest wrote
from the harness that produced the numbers. **`usable` narrows the panel to the points the correlation
accepted**, so the rho and the PBO are two statements about one set of points — which is why the WFC
and the CSCV share this engine and this config rather than two copies of each.
