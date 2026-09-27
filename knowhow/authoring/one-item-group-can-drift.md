---
q: one-item random group still drifts; RandomCondition resolves outside its bound group; template_check 197/200 not 200/200; genetic mutation ignores group membership; fixed condition not always carried
tag: 🔬  date: 2026-09-27  see: authoring/holes-groups-randomcondition, sqx-format/strategy-identity
---
# A one-item group only fixes the FIRST draw; SQX's own mutation can still move the slot later
Binding a `RandomCondition` hole to a group holding exactly one block makes the *initial* pick
deterministic, but it does not freeze the slot for the rest of the run: across many generations a
small fraction of the accepted population ends up with an unrelated native condition in that slot
instead, at `retries="0"` (not a rejected-and-retried pick). `template_check` (post-§60) correctly
flags these as not carrying the fixed block — this is SQX's builder drifting, not a checker bug.

## Evidence
- `Test_USDJPY_donchianUpperCrossUp_M30`, fresh build, 200 accepted of 55,908 generated.
  `template_check --role custodian`: `197/200 carry it — TEMPLATE NOT APPLIED`.
- The 3 strategies (`19.14.48`, `19.16.66`, `8.25.70`): `RandomCondition1` resolved to
  `AroonCrossesAbove` (one case) and other native conditions, each `generated="random"
  randomId="RandomCondition1" retries="0"` — same slot the other 197 fill with
  `CBlock_CloseCrossesAboveDCUpper` from the one-item group `donchianUpperCrossUpSignal`.
- `sqx.inspect.vocabulary donchian` throughout: the block stays installed and pooled by the group on
  both workers — never missing, so this isn't the "block not in this install" failure mode.
- Rate: 3/200 ≈ 1.5% in this run. Not reproduced against a smaller/larger population to see if the
  rate scales; not compared against a template whose hole is bound to a multi-item group.
