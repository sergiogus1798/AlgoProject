---
q: What does the autopilot do when SQX aborts with «Error while running project», and why must the rerun undo first?
kw: Error while running project rerun, autopilot retry once, call.again, call.keeper, Strategy X(1) duplicates, 2,000 strategies for 1,000 built, step 22 IndexError, paso-24-abortado, pass2/ran.json missing
tag: 🔬  date: 2026-10-05  see: sqx-drive/mcr-nullpointer-fastutil-transient
---
# The autopilot reruns SQX's transient abort once — and only after deleting what the aborted attempt added
Trap: the abort comes AFTER «Task finished» and a retest does not clear its output, so a plain rerun doubles
the databank (each strategy twice, the copy named `Strategy X(1)`). Rule: `pipeline/autopilot/call.py` `again`
reruns the action ONCE (SQX step of the restart route, variants' make/execute, closing retests of 23-24);
before a restart-route SQX step `call.keeper` deletes every .sqx the attempt added to the chosen tasks' output
databanks. The live chain does not rerun: it ends the step. Step 24: a failed pass moves the half-done batch to
`<run>/paso-24-abortado` (`closing.py`).

## Evidence
- 🔬 2026-10-05, custodian, smoke run `Test_NIKKEI225_M30_simpleL_ref`: a plain rerun of the OOS retest left
  2,000 strategies for 1,000 built; the dev draw kept 20 instead of 10, every later SQX step computed double,
  step 22 (conditionalMap) (deleted 2026-10-11) died with IndexError (the `(1)` names are not in Results).
- 📓 Sightings: OOS retest (step 7, 01:55, task `OOS`); `WFC 1 IS` in step 24 pass 2 (01:13). Not MC-only.
- 📓 Step 24: pass 1's report alone made the rail call 24 done; step 25 then crashed on missing `pass2/ran.json`.
