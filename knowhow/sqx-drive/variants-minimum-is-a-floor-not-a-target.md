---
q: sqx.variants.make produces way more than 1000 variants; minimum variants config is a floor not a target; how many variants will one mother produce; estimate WFC cost before running variants.execute
tag: 🔬  date: 2026-09-26  see: perf/workflow-step-durations
---
# `minimum.variants: 1000` in `sqx/variants/config.yaml` is a FLOOR, not a target — one mother can produce 1x-5x that with no warning
The config's own comment describes widening integer spans "until [the +/-30% grid] holds
[at least 1000], and whatever is still missing is printed as a shortfall" — this reads as if 1000 is
roughly what to expect. It is not: `minimum.variants` only guarantees the factory will not stop
**below** 1000; the actual count is whatever the full factorial/neighbourhood grid produces once
each parameter clears its own floor, and that combinatorial count has no upper cap or warning.

## Evidence
- 2026-09-26, `USDJPY_workflow_profiling_v1`, three mothers of the same template
  (`crossAboveHMA_v1`), same `minimum.variants: 1000`, `sqx.variants.make` run with defaults on each:
  `Strategy 1.29.55` → **1,093** variants, `Strategy 1.28.59` → **1,457**, `Strategy 1.23.51` →
  **4,999** — a 4.6× spread for the identical config, driven entirely by how many of each mother's
  own parameters had wide-enough integer ranges (more free parameters, or parameters already spanning
  a big range at ±30%, multiply out to more combinations before the 1,000-floor logic ever has to
  widen anything).
- No message, warning, or exit code distinguishes "landed near 1,000" from "landed at 5,000" — only
  `make`'s own progress table (`planned N de un target M`) shows the true count, and it has to be read
  per mother, not assumed from the config.
- Consequence measured downstream: `sqx.variants.execute`'s SQX-side cost for a mother scales with
  this true count once it is large enough (`perf/workflow-step-durations.md` — a WFC leg's fixed
  9-market-loading cost stopped dominating somewhere between ~1,500 and ~5,000 variants). Reading
  only `minimum.variants: 1000` before estimating a run's wall-clock time will under-estimate it by
  up to 5× for a mother whose parameters happen to be wide.
- 🤤 Untested: whether `--min-variants` set lower than 1000 proportionally shrinks the overshoot, or
  whether the overshoot is purely a function of the mother's own parameter count/ranges and
  independent of the floor requested.

**Practical rule**: before launching `sqx.variants.execute` (which burns custodian time and, for a
WFC batch, a look at `oos2`), always read `make`'s own printed count for that specific mother — never
assume it is "around 1,000" from the config alone.
