---
q: which SQX feed per asset DarwTick vs DukasM1 history length; sqx_symbol; SP500ft_Plus02_Infinox missing feed; symbol list
tag: 🔬  date: 2026-09-22  see: costs/refreshing-sqx-costs, locations/logs-and-data-coverage
---
# Use the `DukasM1` feed, not `DarwTick`: tick feeds start 2017–2018, M1 reaches 2003–2012
Six assets were switched to `DukasM1` (owner, 2026-09-22); no cost changed — `InstrumentInfo` is byte-identical between each pair.
`SP500ft` (feed `SP500ft_Plus02_Infinox`, absent from SQX) was retired 2026-09-27: the same index as `USA500` (owner). Back with `core.assetwrite.restore`.

## Evidence
`-symbol action=list` on the conductor; 6 of 17 assets affected:

| asset | was (`*_DarwTick_the5ers`) | now (`*_DukasM1_the5ers`) | gained |
|---|---|---|---|
| `EURUSD`, `USDJPY` | 2017-10-02 | 2003-05-05 | 14 y |
| `AUDUSD` | 2017-10-02 | 2003-08-04 | 14 y |
| `AUDJPY` | 2017-10-02 | 2003-12-01 | 14 y |
| `NIKKEI225` | 2017-10-02 | 2011-09-19 | 6 y |
| `USA500` | 2018-06-27 | 2012-01-19 | 6 y |

- Identical fields: spread, commission, swap, tick size, point value, min distance. Only history length and the `mc_retest` witness differ.
