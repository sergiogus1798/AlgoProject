---
q: Is the blind door scoped per project or per study, and what does backfill --blind cover?
kw: ledger.backfill --blind refuses ya tiene filas de los pasos [19], second project same symbol timeframe template, blind door already open for a new project, step 19 row per project, WFM look not counted, autopilot registers 17 18 19, gate.done study wide
tag: 📓  date: 2026-10-02  see: pipeline/blind-steps-write-no-ledger-rows, pipeline/oos2-door-binds-only-autonomous
---
# The blind door and `backfill --blind` are per STUDY (asset × timeframe × family), not per project
`gate.done`/`allow_read` read the study's whole ledger, and `ledger.backfill --blind --write` refuses
when the study already holds a row of a step it would write. A second project of the same template,
asset and timeframe finds 17-19 «done» before running anything, and its WFM's look at oos2 cannot be
backfilled (`ya tiene filas de los pasos [19]`): uncounted. The autopilot's tail does not call the
command: `pipeline.autopilot.blind.register` writes `from_batch` rows for its own mothers and
`from_wfm` rows once per WFM reading (the row's note names its folder), then asks `allow_read`.
⚠️ Under `ALGO_AUTONOMOUS=1` the door is still the study's: an earlier project's rows open it.

## Evidence
- A step-19 row's note carries `reports/<project>/<WFM>/<day>/wfm`: that is what marks it registered.
- `ledger/gate.py::done` — `set(frame["step"])`, no project in it; `ledger/backfill.py::main` —
  `twice = set(read(study)["step"]) & set(frame["step"])`.
- A live WFC/CSCV row's note is `lote <batch name>`, the mother's folder name with no project:
  two projects with a mother of the same name are one batch to `ledger.blind.recorded`.
- 🔬 `tests/test_autopilot_tail.py`: rows 17 and 18 present, WFM reading on disk → three step-19
  rows written; a second `register` writes none; without the reading, `allow_read` raises
  `faltan [19]` under the flag and no command starts.
- Not run against a real second project; the refusal is read from `backfill.py`.
