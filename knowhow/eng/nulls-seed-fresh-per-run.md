---
q: nulls.seed no fija nada, monkey test same numbers every run, truly different monkeys, 227 and 229 survivors, SeedSequence entropy, reproduce a null run, engines.nulls.inputs.config resolves seed, gate.report survivor count varies, --set nulls.seed override, root seed recorded manifest
tag: 🔬  date: 2026-09-29  see: perf/python-parallelism, sqx-format/leg-curve-warmup
---
# `nulls.seed: null` by default — a fresh root every run, recorded so it can be replayed
Issue 45, owner 2026-09-29: "quiero un test del mono truly different". `nulls.seed` in `engines/nulls/config.yaml` defaults to `null`; `engines.nulls.inputs.config()` resolves it once per process, before any fork, to `int(np.random.SeedSequence().entropy)` when null, and keeps an explicit int (config.yaml or `--set nulls.seed=<int>`) as given.
`simulate.nulls()` still derives every block from `SeedSequence([root, _stable(key), rung_id, i])`: independence holds, only the root differs run to run. Every caller records the root it drew.
Other modules' own `seed:` (`cscv`, `wfm`, `blindJoint`, `snoopingScreen`, `crossmarket`) are separate, fixed on purpose — this card is `engines/nulls/config.yaml` only.

## Evidence
- Recorded where: `studies.readings.monkey.one.run`'s `summary.nulls_seed`, `many.run`'s
  population note, `monkey/report.py`'s and `gate/report.py`'s `manifest.json`
  `source.seed`/`source.nulls_seed`, `crossTF/report.py`'s manifest via `core.study.verdicts.
  write(..., extra={"nulls_seed": ...})`. Reproduce with `--set nulls.seed=<the recorded int>`
  (gate has no CLI passthrough today — edit `config.yaml`'s `seed:`, or call
  `engines.nulls.inputs.config(["nulls.seed=<int>"])` directly).
- `_stable()`'s blake2b hash (the 2026-09-25 fix for `hash()`'s per-process salt, once
  responsible for two gate runs reading 227 and 229 survivors from identical files) is what makes
  a *fixed* seed reproduce a run at all, and what makes two strategies in the same run draw
  different monkeys under a fresh root instead of clones of each other's stream.
- 🔬 `python3 -c "from engines.nulls import inputs; print(inputs.config([])['nulls']['seed'],
  inputs.config([])['nulls']['seed'])"` — two calls in the same process print two different
  128-bit ints; `inputs.config(['nulls.seed=42'])['nulls']['seed'] == 42`.
- 🔬 `core.study.config.apply`'s `_cast` special-cases `old is None`: a `--set nulls.seed=<int>`
  override works against the `null` default without touching the type-check that refuses a
  threshold changing type on the command line.
- Not measured: two `studies.screening.gate.report` runs over the same harvest, survivor count
  before/after — no stored harvest was reachable without SQX in this task; the 227-vs-229 spread
  the pre-2026-09-25 `hash()` bug produced (same order of magnitude of noise) is the closest
  measured analogue, and a fresh root should move individual strategies' p across the `alpha`
  line at a similar rate since nothing about the null distribution itself changed.
