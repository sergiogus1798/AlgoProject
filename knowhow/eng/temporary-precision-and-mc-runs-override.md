---
q: how to run one project tonight at a different precision or MC Retest count without touching `_build.yaml`, and how to restore it
tag: 🔬  date: 2026-09-29  see: eng/feed-in-config-yaml

# `ALGO_PRECISION_OVERRIDE` / `ALGO_MC_SIMULATIONS` — a run-wide, one-project override

Every configurator reads precision and MC Retest run count from `core.assetdata.doctrine()`
(`_build.yaml` alone). These two env vars, read only inside `doctrine()`, replace every occurrence
in the returned tree (`core.assetoverride.replace`, a generic recursive walk by field name): every
`precision` (build, default, the builder's `RetestWithHigherPrecision` cross-check, every retest,
every MC Retest/SPP task) or `simulations` (the shared default and each MC Retest task's own).
Set the variable only for the ONE configurator call that stages that one project's step, never for
`sqx.projects.builder` itself — the Build/OOS tasks must keep the real doctrine. `_build.yaml` never
changes, so restoring is simply not setting the variable next time.

## Evidence
- 🔬 2026-09-29: `ALGO_PRECISION_OVERRIDE=1 ALGO_MC_SIMULATIONS=200 python3 -c "from core.assetdata
  import doctrine; print(doctrine())"` — every `precision` in the tree read `1`, `mc_retest.simulations`
  and each of its 8 tasks' own `simulations` read `200`; unset, `doctrine()` reproduced the file exactly
  (`precision.build=1, default=2`, `crosschecks.precision=3`, SPP's own `precision=1` unchanged).
