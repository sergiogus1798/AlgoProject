# studies/transfer/crossmarket — step 10: does the logic travel?

One study, one folder. Step 10 asks whether a strategy's rule keeps working on markets it was never
optimised on. The answer is nine facts (P1-P9) per strategy; the lines that turn them into Pasa /
Limbo / Falla are `pipeline/autopilot/criteria.yaml` (step 10), never code here. Spec and history:
`docs/encargos/46-paso-10-otros-mercados-la-logica-viaja.md`.

How it is judged, in one paragraph. Every market is priced in R at the doctrine's size. The real
run and `travel.draws` random runs (the same trades shifted by whole weeks inside each calendar
year, one shift per year shared by all markets) fill one tensor `(runs, markets, cells)`; every z —
joint, per window V0/V1/V2, per market, all-but-one, per year — is read from it. Cost in R does not
cancel for ATR-conditioned entries, so z is read on gross R (`travel.judge_on`).

```
many.py / one.py / report.py ──▶ travel/run.py ──▶ verdict.csv, markets.parquet, crossmarket.json, distribuciones.parquet
                                   │  cells, sizing, shift, tensor, stat   (the machinery)
                                   └─ rules, frequency, validity, units    (P1-P9 and the §7.1 controls)
```

| path | what it does | run it |
|---|---|---|
| `report.py` | The command: every strategy of one export, or one (`--strategy`) in full | `python3 -m studies.transfer.crossmarket.report --project P --databank D --asset A` |
| `many.py` | The population result: `travel.run`'s files read as one table | imported |
| `one.py` | One strategy across every market, as the contract's blocks the window paints | imported |
| `load.py` | Everything one run reads: trades, bars, the export's identity map | imported |
| `config.yaml` | Every knob, under `travel:`; `tooltips.py` has one sentence per knob | edit or `--set travel.key=v` |
| `travel/` | The test itself (own README) | imported |
| `inputs/` | `config.py` (reads `config.yaml`) and `markets.py` (the export's markets against `assets/_markets.yaml`) | imported |
| `contract/tabs.py` | The strategy's tabs: numbers by test, each market, yearly edge, warnings | imported |

Traps. The market list is fixed before results are looked at (`assets/_markets.yaml` classifies,
the export decides what exists). `config.yaml` stays in this folder: `inputs/config.py` resolves it
as `parents[1]`. The old study (nulls per market, Fieller, breadth, paired tests) was replaced on
2026-10-07 and deleted; `knowhow/research/` keeps what it measured, marked as retired.
