# walkForwardCorrelation/inputs — what the study is run on

| file | what it does | in → out |
|---|---|---|
| `config.py` | Reads the module's `config.yaml`, the single place every knob lives | — → settings |
| `panel.py` | The N × T panel the CSCV runs on, and where the real in-sample boundary is | `equity.parquet` → panel, windows |

Holds nothing computed.

**The IS/OOS boundary is not a setting here.** `split` reads it off `equity.json`, which the harvest
wrote from the harness that produced the numbers. One date, one definition: a boundary re-declared
in `config.yaml` would drift from the one the retest actually used and nothing would complain.

**`usable` narrows the panel to the variants the correlation already accepted**, so the rho and the
PBO are two statements about one set of points rather than two samples that happen to share a name.
That is why it takes `metrics` and `min_trades` rather than filtering on the curves themselves.
