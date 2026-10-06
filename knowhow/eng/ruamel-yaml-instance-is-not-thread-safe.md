---
q: Why does a daemon endpoint that reads an asset YAML fail now and then with a ruamel parser error?
kw: ruamel YAML() shared instance thread safe, ParserError ScannerError intermittent, flaky test_ui_shell, FastAPI thread pool, core.assetyaml _Y load dump, concurrent requests asset yaml, threading.Lock
tag: 🔬  date: 2026-10-06  see: editing-asset-yaml
---
# One ruamel `YAML()` instance cannot load from two threads at once
A `ruamel.yaml.YAML()` object keeps its reader, scanner and parser as state: two `load` (or `dump`) calls on the
same instance from different threads corrupt each other and raise a parser error on a file that is fine. The
daemon answers sync endpoints from a thread pool, so any module-level instance is shared. `core.assetyaml`
holds `_LOCK` around `_Y.load` and `_Y.dump`; a new module-level `YAML()` needs the same, or goes through `core.assetyaml`.

## Evidence
- 🔬 2026-10-06: `tests/test_ui_shell.py` failed about one run in several (nightly audit, `OPEN.md` #95) when the window fired
  parallel requests that each read an asset card; with the lock in `core/assetyaml.py` it passes repeatedly.
