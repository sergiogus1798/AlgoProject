---
q: which XML element is the SPP; OptProfileSysParamPermutation vs SequentialOptimization; SPP defaults MaxTests DistributionUp Steps WhatToParametrize; SPP writes no profile
tag: 🔬  date: 2026-09-22  see: sqx-drive/spp-headless, export/spp-export, sqx-format/optimization-profile-bin
---
# The SPP is `OptProfileSysParamPermutation`; `SequentialOptimization` writes no profile
Both sit in a retest task's `<CrossChecks>`; only the first is the SPP. Enabling the wrong one
burned 47 cores for 91 min, RSS 23.6→43.3 GB, 0 tested, no `optimizationProfile.bin`.
Owner's defaults unless he names others: `MaxTests` 15,000 (10,000 ok; never inherit `1000000001` =
exhaustive), `DistributionUp/Down` 35 or 40, `Steps = round(2*spread/4)` (18 at ±35, 20 at ±40),
`WhatToParametrize type="0"` with only `Recommended` true.

## Evidence
| element | what |
|---|---|
| `OptProfileSysParamPermutation` | the SPP; writes the optimization profile |
| `SequentialOptimization` | walks parameters one at a time for a better setting; no profile |
Why: ±30 too narrow; ~4 % a step (12 steps over ±30 = 5 %, coarse); hand-picked families permute
what the strategy doesn't key on.
Everything else (IS/OOS window, Friday close, money management, exits, spread) must match the build:
build the task by copying one the owner runs, replace only the cross-check block and databanks.
Skill: `tools/sqx-lab/plugins/sqx-lab/skills/sqx-spp/SKILL.md`. Code: `sqx/variants/harness.py`.
