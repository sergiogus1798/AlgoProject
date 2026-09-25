---
q: resumable pipeline job, ledger vs outputs on disk vs sha256, skip a finished stage, atomic write os.replace same directory, kill test SIGKILL process group killpg, progress bar test monotonic, shlex.split template spaces, PROGRESS stdout protocol
tag: 🔬  date: 2026-09-21  see: eng/pipeline-run-guards
---
# A resumable job: ledger + outputs present + outputs unchanged (sha256) are three separate facts
- Skip a stage only if the ledger says done AND its outputs are on disk (`pipeline/stages/gates.py`); the ledger outlives data on purpose.
  Cleanup/trust needs the third: re-hash against the recorded sha256 (`pipeline/cleanup.py`).
- Atomic state: temp file in the SAME directory + `os.replace` (atomic only within one filesystem; AlgoData may differ from the repo).
- Kill tests: `start_new_session=True` + `os.killpg(os.getpgid(pid), SIGKILL)`, never the child alone.
- Split a command template (`shlex.split`) before formatting tokens, never after. Stages join via stdout `PROGRESS <0..100> <status>`.

## Evidence
`pipeline/verify/selftest.py`.
- Skipping on ledger alone: a mother whose variants were swept would look unfinished → rebuild 5,000 variants for a verdict already held.
- A thread reading `state.json` every 20 ms while five stages wrote via temp+`os.replace` never saw a partial file. Plain `write_text` truncates first.
- Killing only the child left the stage's subprocess writing progress into a dead pipeline's ledger (passes for the wrong reason).
  Group kill: stage died at 20 %, `state.json` parsed, stage not marked finished; relaunch skipped the done stage, redid the killed one.
- Progress test: an outside reader must see ≥ 2 distinct intermediate values (`pipeline/verify/monotonic.py`); 0-then-100 is monotonic and is the failure.
  Enforce monotonicity by raising, not clamping (clamping hides repeated work as a still bar).
- `shlex.split(template.format(...))` turns `--strategy Strategy 17.9.39` into three args (same trap as CLAUDE.md rule 6).
- Any other stdout becomes the status without moving the bar. `strategies.sppUltra` doesn't know the protocol, still shows live status, progress 0 → 100 at end.
  An import contract would have blocked three agents writing modules concurrently.
