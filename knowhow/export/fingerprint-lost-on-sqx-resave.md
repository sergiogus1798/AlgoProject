---
q: Why is the Results export redone at step 19 although the databank did not change?
kw: sources.sig changes, fingerprint mismatch, stale export, re-export Results step 19, load and re-save, afterrun stale, liverun.export
tag: 📓  date: 2026-10-12  see: sqx-drive/export-after-every-stop, databanks/exit-regrabs-loaded-databanks-by-session-age
---
# The export fingerprint does not survive SQX «load from file and re-save»
Trap: a databank SQX loaded and re-saved (the exit regrab) gets a new fingerprint although its strategies are the same, so it counts as stale and is exported again: Results (10,000) at step 19 in 4 of 4 runs, ~155 s plus ~30 s for OOS and Retest Markets; not at step 15, where the exit had not regrabbed it. Which zip member changes is unknown (no «before» file is left). Fix idea: `liverun.export` (`sqx/databank/state.py:149`, `liverun.py:141`) exports only the step's outputs, not all «stale» (`afterrun.py:127`). Dropping the reopen (see the linked card) removes the Results case.

## Evidence
- 📓 `findings-SQXPY.md` SQXPY-2. In `Test_XAUUSD_H1_ruptura_mcptR` today's Results fingerprint matches no saved `.sources.sig`; alone this does not rule out a real change.
- 🤔 Confirm by exporting, re-saving in SQX and diffing zip members' CRCs (experiment E3).
