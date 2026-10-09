# wfc/measure — the numbers

Pure functions on arrays: no batch, no file, no config beyond the dict handed in. The calibration
(`../calibrate/`) drives the same functions with synthetic families.

| file | what it does | in → out |
|---|---|---|
| `order.py` | The partial rho on rank residuals (annotated). Spearman, the sign draws and the tails are `engines/weekly/flip.py`'s | excess → rho |
| `level.py` | The in-sample top, its `p_value` in the flipped draws, the selection premium (median of the top − median of all) and `R_sel`, refused when the in-sample premium is nearly null | excess → mask, premium, R_sel |
| `reading.py` | One composition read whole: the order on **gross** excess against the weekly sign-flip null (one sign per week for every variant; again in wider blocks when too many trades straddle a weekend), and on **net** excess with the same signs the top's level, `p_nivel`, `R_sel` with its null range and the four quadrants | e_is, e_oos, weeks (each `gross` and `net`) → facts |

Holds no word of a verdict: `positivo`, `pasa` and the rest are `../verdict/`'s.

**A rho that is not a number must never reach `tails`.** With a constant side every null rho is
NaN too, no draw compares as `>=`, and both p read 1/(draws+1): «positivo» and «perverso» at once.
`verdict.state.classify` answers `sin_dato` first.
