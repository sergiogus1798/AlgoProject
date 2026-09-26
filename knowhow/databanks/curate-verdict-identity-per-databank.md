---
q: apply_verdict refuses OOS with different strategy than verdict judged; identidad distinta IS OOS; curating both Results and OOS with one verdict.csv; 3 con identidad distinta harvest
tag: 🔬  date: 2026-09-26  see: authoring/cloned-custom-block-native-key
---
# A verdict's `identity` column is per-DATABANK, not per-strategy-name: applying the same verdict.csv to Results and OOS can refuse on OOS
`gate.harvest` already flags it ("N con identidad distinta") but it is easy to read as a warning
that does not block anything. It does block: `apply_verdict` hashes the file it is ABOUT TO DELETE
and compares it to the verdict's `identity` column. A `verdict.csv` written from `Results`' own
metrics/identities carries `Results`' hashes. Applying that same file to `OOS` fails for exactly the
strategies whose IS/OOS identity differs — `apply_verdict` reports them by name and **moves nothing
at all for that run** (all-or-nothing, not partial).

## Evidence
- Encargo 21, `USDJPY_workflow_profiling_v1`, artificial net-profit cut 96→8 (aforo cut, not a gate
  verdict). `sqx.curate.verdict --keep net_profit_is>=60000.89` on `Results` produced
  `verdict-094650.csv`; `apply_verdict --databank OOS --verdict <that file>` (dry run) reported
  `✗ 3 carry a different strategy than the verdict judged: Strategy 20.1.85, Strategy 21.6.85,
  Strategy 21.7.57` — the same three the harvest step had already counted as "3 con identidad
  distinta" out of 200 pairs, half an hour earlier in the same run.
- None of the 3 were among the 8 kept, so the mismatch was harmless here, but `apply_verdict`
  refused the WHOLE OOS apply anyway (0 of 96 moved), not just those 3 — nothing partial.
- Fix used: regenerate a databank-specific verdict — same `strategy`/`verdict`/`reason` columns,
  but `identity` recomputed with `core.sqxfile.identity()` against the **OOS** databank's own files
  for each name, before calling `apply_verdict --databank OOS` with that file. Applied cleanly:
  `identity checked on 88 of 88`.
- The gate's real verdict (200→96, same run) never hit this: harvest paired 200/200 by name with
  only 3 identity mismatches, and none of those 3 were split across the MANTENER/DESCARTAR boundary
  in either cut, so re-using the IS-identity verdict.csv on OOS worked there. It is luck, not a
  guarantee — the failure mode reappears whenever one of the mismatched names lands in either
  databank's delete list.
- 🤔 Untested: whether `gate.report`'s own verdict.csv should carry TWO identity columns
  (`identity_is`, `identity_oos`) so `/curate` can apply it to either databank without
  re-deriving one; today the skill's own worked example (`docs manual`) shows a single verdict
  reused across Results and OOS as if it always just works.
