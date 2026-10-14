---
q: Why does checks.py miss absolute paths in bin/*.sh, and why does mapfile < <(...) lose the exit status?
kw: ratchet.json key absent saved not flagged, ruff failed run read as 0, ruff format --check Would reformat missing unformatted concise, checks.py absolute path in bin/*.sh, checker input files, hardcoded_paths, mapfile process substitution exit status lost, bash KeyError three lines
tag: 🔬  date: 2026-10-14  see: eng/windows-portability, eng/moving-module-into-layer
---
# A checker only sees the files it is handed; `mapfile < <(...)` drops the exit status
- A documented manual workaround for a rule means the checker's input is wrong, not its rule.
  `hardcoded_paths()` in `tools/checks.py` now scans `.py` + `bin/*.sh`.
- In bash, capture a helper with command substitution (keeps `$?`), then `mapfile` from the string.
  Never validate by line count.
- A ratchet must fail closed: `tools/ratchet.py` once saved a key absent from `ratchet.json` instead of flagging it, and read a failed ruff/pyright run (exit > 1 or empty stdout) as 0 and saved that as a fall. Now every key compares against `old.get(k, 0)`, the zero-keys are seeded, a failed run raises, and `except (Exception, X)` counts as broad (fixed in `1bc2194`).
- ruff 0.16 `ruff format --check` prints rich diagnostics, not `Would reformat:`. Parse `--output-format concise` lines `path:l:c: unformatted: ...` (`unformatted` in `tools/checks.py`).

## Evidence
- 📓 `tools/checks.py` checked "no absolute path outside `core/paths.py`" over `depmap.py_files()` = only `.py`.
  `bin/sqx-worker.sh`, `bin/clone-sqx-worker.sh` carried `/home/sergioguslw/Desktop/SQX` for months in
  green builds; `docs/SETUP-NEW-MACHINE.md` grew a "⚠️ edit these two files first" step. Same regex works on bash (`#` comments).
- 🔬 `mapfile -t X < <(python3 -c ... 2>&1)` discards `$?`. "Trust if 3 lines" fails: a `KeyError`
  traceback from `python3 -c` is exactly three lines → unknown worker role ran with an empty install path. Fix:
```bash
_W=$(python3 -c '...' "$ROLE" 2>&1) || { printf 'cannot resolve %s:\n  %s\n' "$ROLE" "$_W"; exit 1; }
mapfile -t _W <<< "$_W"
```
