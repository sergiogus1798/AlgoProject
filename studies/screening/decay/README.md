# screening/decay — how much of each strategy's in-sample edge survived

| file | what it does | run it | in → out |
|---|---|---|---|
| `report.py` | Per strategy: Sharpe in and out, retention, the t of what is left, positive years, concentration, and MANTENER / DUDOSA / DESCARTAR; the population read per verdict and per template. `--is-databank Results`: the IS curve from the build it retested, paired by name — a workflow keeps IS and OOS in two databanks, and alone the OOS one gave every `sharpe_is` empty (📓 2026-09-30); the window's runner passes it (`ui.daemon.loader.find.built_from`) | `python3 -m studies.screening.decay.report --project P --databank OOS --split 2018-01-01 --end 2022-12-31 --role custodian --is-databank Results [--strategy "Strategy 1.2.3"]` | the databank's `.sqx` → `reports/<P>/<D>/<date>/decay/` (`verdict.csv` with identity); with `--strategy` only `estrategias/<name>.json/.html` — never `decay.json`, `verdict.csv` or the manifest, which are the population's (no duplicate is dropped: that is a population fact) |
| `one.py` | One strategy's decay as the contract: its verdict (MANTENER / DUDOSA / DESCARTAR with its meaning), its numbers — the same row `verdict.csv` gives it — and its OOS P&L per year | imported by `report.py --strategy` | curve → contract dict |

The maths is `../analysis/decay.py`, which the gate's degradation screen reads too.
