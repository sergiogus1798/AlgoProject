# screening/decay — how much of each strategy's in-sample edge survived

| file | what it does | run it | in → out |
|---|---|---|---|
| `one.py` | One strategy's decay as the contract's data: its verdict, its numbers and its OOS years. | imported by `report.py --strategy` | curve → contract dict |
| `report.py` | Judge every strategy in a databank on how much of its in-sample edge survived out of sample. | `python3 -m studies.screening.decay.report --project P --databank OOS --split 2018-01-01 --end 2022-12-31 --role custodian --is-databank Results [--strategy "Strategy 1.2.3"]` | the databank's `.sqx` → `reports/<P>/<D>/<date>/decay/` (`verdict.csv` with identity); with `--strategy` only `estrategias/<name>.json/.html` — never `decay.json`, `verdict.csv` or the manifest, which are the population's (no duplicate is dropped: that is a population fact) |

The maths is `../analysis/decay.py`, which the gate's degradation screen reads too.
