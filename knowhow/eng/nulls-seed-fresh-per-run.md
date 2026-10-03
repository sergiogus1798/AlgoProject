---
q: How do I replay a null run, given nulls.seed is null by default?
kw: nulls.seed no fija nada, monkey test same numbers every run, truly different monkeys, 227 and 229 survivors, SeedSequence entropy, reproduce a null run, engines.nulls.inputs.config resolves seed, gate.report survivor count varies, --set nulls.seed override, --seed flag monkey gate reproducible p-values, monkey p as outcome calibration, mono_seed nulls_csv.seed fact, root seed recorded manifest
tag: 🔬  date: 2026-10-02  see: perf/python-parallelism, sqx-format/leg-curve-warmup
---
# `nulls.seed: null` by default — a fresh root every run, recorded; `--seed N` replays it
Issue 45, owner 2026-09-29: "quiero un test del mono truly different". `nulls.seed` in `engines/nulls/config.yaml` defaults to `null`; `engines.nulls.inputs.config()` resolves it once per process, before any fork, to a fresh **32-bit** root when null, and keeps an explicit int as given.
Reproduce: `--seed <int>` on `studies.readings.monkey.report` and `studies.screening.gate.report` (2026-10-02), or `--set nulls.seed=<int>` where a command has `--set` for the engine. **A study that uses the monkey's p as an outcome must pass `--seed`**: the default is the owner's and stays fresh.
`simulate.nulls()` derives every block from `SeedSequence([root, _stable(key), rung_id, i])`: a strategy's p depends on the root and its own name/identity only — not on process order, worker count or batch.
Other modules' own `seed:` (`cscv`, `wfm`, `blindJoint`, `snoopingScreen`, `crossmarket`) are separate, fixed on purpose — this card is `engines/nulls/config.yaml` only.

## Evidence
- Recorded where: `studies/readings/monkey/report.py` — `manifest.json` `source.seed` and `--seed` inside `command`,
  `nulls.csv` column `seed` (fact `monkey.nulls_csv.seed`), last stdout line; `one.run`'s
  `summary.nulls_seed`; `many.run`'s population note. `studies/screening/gate/report.py` — manifest
  `source.nulls_seed` and `command`, scorecard `mono_seed` (fact `gate.scorecard.mono_seed`),
  last stdout line. `studies/transfer/crossTF/report.py`'s manifest via `core.study.verdicts.write(..., extra=)`.
- 🔬 2026-10-02, `Test_XAUUSD_timeRangeBreakout3_M30` (300 strategies, 101 k OOS trades), two runs
  with `--seed 20261002`: monkey's `nulls.csv`, `manifest.json`, `rungs.json` byte-identical
  (`monkey.json/.md/.html` differ only in `computed_at` and `wall_s`); gate's `scorecard.parquet`,
  `verdict.csv`, `verdict_build.csv`, `funnel.csv`, `manifest.json` byte-identical. `--seed 5`
  moves `nulls.csv`. Same p as the code before the flag under `--set nulls.seed=20261002`.
  Cost: none — monkey 3.3 s and gate 3.2-3.3 s before and after. `tests/test_nulls_seed.py`.
- 🔬 The fresh root was `SeedSequence().entropy`, 128 bits, until 2026-10-02: exact in
  `manifest.json` but not through a float — a facts line or a parquet/CSV numeric column rounds
  it past 2**53 and the run cannot be replayed from there. Now `generate_state(1)[0]`, 32 bits.
  An old manifest's 128-bit seed still replays: an explicit int is passed through untouched.
- `_stable()`'s blake2b hash (the 2026-09-25 fix for `hash()`'s per-process salt, once
  responsible for two gate runs reading 227 and 229 survivors from identical files) is what makes
  a *fixed* seed reproduce a run at all, and what makes two strategies in the same run draw
  different monkeys under a fresh root instead of clones of each other's stream.
- 🔬 `python3 -c "from engines.nulls import inputs; print(inputs.config([])['nulls']['seed'],
  inputs.config([])['nulls']['seed'])"` — two calls in the same process print two different
  ints; `inputs.config(['nulls.seed=42'])['nulls']['seed'] == 42`.
- 🔬 `core.study.config.apply`'s `_cast` special-cases `old is None`: a `--set nulls.seed=<int>`
  override works against the `null` default without touching the type-check that refuses a
  threshold changing type on the command line.
- Not measured: two `studies.screening.gate.report` runs over the same harvest, survivor count
  before/after — no stored harvest was reachable without SQX in this task; the 227-vs-229 spread
  the pre-2026-09-25 `hash()` bug produced (same order of magnitude of noise) is the closest
  measured analogue, and a fresh root should move individual strategies' p across the `alpha`
  line at a similar rate since nothing about the null distribution itself changed.
