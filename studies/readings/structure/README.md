# structure — which entry condition carries the edge, and whether it lives in the direction

Encargo 12, the statistical half: workflow step 23, one reading per surviving strategy. It reads
the batch `sqx/structural/` fabricated and the custodian retested: the mother rebuilt, one ablation
per entry condition, the inversion. **Diagnostic, never selection** (§5): an ablation that reads
better is a condition that did not help, not a strategy to adopt. No `many.py`: the study judges no
population, it describes one strategy at a time.

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.yaml` | Every knob: random-subset draws and seed, the test's alpha, the controls' tolerances | edited | — |
| `tooltips.py` | One Spanish sentence per knob, for the window's drawer | imported | — |
| `inputs.py` | The knobs, the batch's plan and retention check, every file's trades per leg — each leg cleared by `ledger.gate.allow(23, …)` first | imported | batch + exports → dict |
| `measure.py` | The numbers: per-trade ΔM and the random-subset null per ablation, the inversion's pairing and its split into move at mid, spread and carry, the identity rebuild against what the mother stored | imported | trades → dicts |
| `reading.py` | The words a measurement earns, each with its state and its sentence | imported | dict → label |
| `contract.py` | The three tabs: each condition's ΔM, the inversion, the controls; one leg per selector option | imported | dicts → tabs |
| `one.py` | `run(strategy, got, cfg)`: one mother's result per `core/study/CONTRACT.md` | imported | → dict |
| `report.py` | The command: every mother of the batch, printed and written | `python3 -m studies.readings.structure.report --work <batch> --project <P> --databank WFC_Build WFC_OOS1 --feed <feed> --symbol <SYM>` | → `<batch>/estudios/structure/` |

## Why ΔM is per trade, and why the null is not `filter.benchmark` itself

Deleting a filter changes the trade count, so total profit compares two sample sizes and always
flatters the one that trades more. ΔE (expectancy) and ΔSharpe are per trade, as in
`engines/nulls/filter.py`, whose `STATISTICS` this module uses.

`filter.benchmark` assumes the filtered trades are a subset of the unfiltered ones. A strategy that
holds one position at a time breaks that: when the mother's entry comes, the ablation is usually
already inside a trade it opened earlier. Measured on `Strategy 23.1.53`: **2 %** of the mother's
entries have a twin in the ablation. So the null keeps `filter`'s question — is the mother better
than the same number of the ablation's trades taken at random? — and takes the mother's own list as
the observed value (`measure.subset_null`). The twin share is shown beside it.

## oos2

`inputs.load` asks the ledger's one-way door for every leg. `_policy.yaml` reserves `oos2` for the
WFC and the WFM, so `--databank WFC_OOS2` is refused at step 23 (PermissionError, no file opened).
Widening that is the owner's call in `_policy.yaml`, not a flag here.
