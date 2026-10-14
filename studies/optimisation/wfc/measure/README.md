# wfc/measure — the numbers

Pure functions on arrays: no batch, no file, no config beyond the dict handed in. The calibration
(`../calibrate/`) drives the same functions with synthetic families.

| file | what it does | in → out |
|---|---|---|
| `level.py` | Does what an optimiser would pick win out of sample: the in-sample top and its out-of-sample median. | excess → mask, premium, R_sel |
| `order.py` | What is left of the in-sample order out of sample once a shared control is taken out: the partial rho. | excess → rho |
| `reading.py` | Every number of one in-sample / out-of-sample composition: the order on gross excess, the level on net. | e_is, e_oos, weeks (each `gross` and `net`) → facts |

Holds no word of a verdict: `positivo`, `pasa` and the rest are `../verdict/`'s.

**A rho that is not a number must never reach `tails`.** With a constant side every null rho is
NaN too, no draw compares as `>=`, and both p read 1/(draws+1): «positivo» and «perverso» at once.
`verdict.state.classify` answers `sin_dato` first.
