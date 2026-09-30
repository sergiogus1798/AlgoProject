---
q: CrossTF Input has no strategies nothing to test; CrossTF databank empty; No columns to parse from file; Databanks view stuck on Cross TF; empty metrics.csv 1 byte; step 10.5 preparation; who fills CrossTF_Input; CrossTF_Mothers; MC Retest reads Results; Cross Market → Cross TF → MC Retest order; crosstfload
tag: 🔬  date: 2026-09-29  see: databanks/curating-a-databank, sqx-drive/start-before-databanks-load, sqx-drive/custom-timeframe-h12
---
# `CrossTF_Input` is written by no task: something must fill it on disk before step 11, or Cross TF tests nothing
Every other retest reads a task's output; `CrossTF` reads `CrossTF_Input`, which only a preparation fills
(the Cross Market survivors scaled, plus the mothers). Until 2026-09-29 that was chat-only, so the window
refused 11 («no tendría nada que probar»), CrossTF never ran, its databank stayed empty, and
`export_metrics` wrote a 1-byte `metrics.csv` whose `read_csv` raised inside `/api/databank/panels`,
killing every tab. Now `sqx.projects.crosstfload` fills it with the install stopped (SQX loads the files on
start) from inside the launch of 11, and fills `CrossTF_Mothers` (mothers without `_Scaled*` siblings)
before 13 — the eight MCR tasks of a `--workflow` project read that, not `Results`.

## Evidence
- `Test_USDJPY_donchianUpperCrossUp_M30` on SQX_w2: every global_log shows `CrossTF_Input (0)`, `CrossTF (0)`;
  no «Task: CrossTF» line. MCR 1-8 ran 2026-09-29 06:48 with Input `Results` (the mcretest `--input`).
- `AlgoData/metrics/<P>/CrossTF/metrics.csv` = `\n`, manifest `worker_saw: 0`. `pd.read_csv` →
  `EmptyDataError: No columns to parse from file`, raised via `layout.splits → table.table → metrics.export`.
- The only fabrication, `AlgoData/crosstf/<P>/2026-09-27/`, predates the project folder (2026-09-28 12:07).
- Fix verified on `Test_USDJPY_crosstfDiag_H1` (conductor): `ui.daemon.launch.run --step 11` filled 12
  .sqx (3 mothers + M30/H4/D1 siblings), SQX loaded them at start, CrossTF 0 → 12, export 12 rows ×
  38 columns + 19 154 trades, `crossTF.report` read every cell; `--mothers` put 3 in CrossTF_Mothers.
- The 3 test mothers made 0 trades on D1 even unscaled: D1 cells can be empty, not only clamped.
- H1→M30 (ratio 0.5) doubles periods: shift 0, never clamped. H1→D1 clamps nearly all (shift 2–15).
- `core.assetwrite.set_value` replacing a list node dropped the 60-line comment block after it (ruamel
  keeps trailing comments on the last node): check `git diff` after writing a sequence.
