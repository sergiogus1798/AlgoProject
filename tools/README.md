# tools — project maintenance

| file | what it does | run it |
|---|---|---|
| `checks.py` | Verify every mechanical rule in `CODESTYLE.md` and list what breaks them | `python3 tools/checks.py` |
| `depmap.py` | Read the real imports and regenerate `docs/DEPENDENCIES.md` | `python3 tools/depmap.py` |
| `skillmap.py` | Read every installed skill and regenerate `docs/SKILLS.md` — what exists, what it costs to invoke, what is stale | `python3 tools/skillmap.py` |
| `knowhowmap.py` | Regenerate each `knowhow/<domain>/INDEX.md` from its cards' `q:` lines; `checks.py` uses it to check the cards, the `knowhow/` links and the indexes | `python3 tools/knowhowmap.py` |
| `manual.py` | Build the user manual as one PDF per workflow family, from the chapters in `AlgoData/manual-fuentes/` | `python3 tools/manual.py` |
| `daily_audit.py` | The half of the audit a machine can do alone: checks, tests, corrupt projects, missing manifests, undecided asset costs | `python3 tools/daily_audit.py` |
| `uiwalk.py` | Dev-only: open every zone of the window offscreen against a running daemon, drive its combos, tabs and tables with every write refused (POSTs answered here, `/api/load` read as its GET, modals «No»), and report each exception by zone; exits 1 when anything raised | `QT_QPA_PLATFORM=offscreen python3 tools/uiwalk.py --port P` |

`manual.py` renders the chapters to `docs/manual/NN-<family>.pdf` through headless Chrome, whose path lives in `config/machine.yaml`. The owner reads only PDFs (2026-09-26): the PDFs are in git and are the only thing in `docs/manual/`; the `.md` chapters and their `assets/` are the original and live in `AlgoData/manual-fuentes/`, out of the repo. `FAMILIES` decides which chapter goes in which PDF, and a chapter in no family stops the build. A family is rendered again only when its HTML or a picture it shows changed (`AlgoData/manual-fuentes/.rendered.json`; delete it to force a full rebuild) — `knowhow/eng/manual-pdf-rebuild-is-input-keyed.md`.

`daily_audit.py` writes `AlgoData/audit/YYYY-MM-DD-mechanical.md` (`core.paths.AUDIT`) and exits non-zero when something regressed.
It involves no model. **It is installed**, as the first half of `bin/nightly-audit.sh`, which cron
runs at 03:00 and which then runs the `auditor` agent headless on Sonnet for the judgement half.
`bin/nightly-docs.sh` runs the `documenter` the same way at 03:30, after waiting for the audit's
lock, and leaves its repairs uncommitted. `bin/nightly-fix.sh` runs the `fixer` on Opus at 04:00,
after the documenter, in the one checkout, and leaves its fixes uncommitted too — the owner commits
what he wants. `bin/nightly-sync.sh` is the same shape for `/sync`. Why the `claude` they call is found the way it
is: `knowhow/eng/headless-claude-from-cron.md`.

`sqx-lab/` is a vendored plugin, not project code: four skills that author custom blocks, random
groups, strategy templates and build projects. **Its path must not move** — `~/.claude/skills/sqx-*`
and `~/.claude/sqx_common.py` are symlinks into it, and `/sqx-setup` and `/sqx-doctor` name it
literally. `checks.py` and `depmap.py` skip it.

Run both tools after touching any Python:

```bash
python3 tools/depmap.py && python3 tools/checks.py
```
