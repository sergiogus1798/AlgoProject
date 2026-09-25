# screening/decay — how much of each strategy's in-sample edge survived

| file | what it does | run it | in → out |
|---|---|---|---|
| `report.py` | Per strategy: Sharpe in and out, retention, the t of what is left, positive years, concentration, and MANTENER / DUDOSA / DESCARTAR; the population read per verdict and per template | `python3 -m studies.screening.decay.report --project XAUUSD --databank OOS --split 2018-01-01 --end 2022-12-31` | the databank's `.sqx` → `reports/<P>/<D>/<date>/decay/` (`verdict.csv` with identity) |

The maths is `../analysis/decay.py`, which the gate's degradation screen reads too.
