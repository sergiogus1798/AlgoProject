# tools — project maintenance

| file | what it does | run it |
|---|---|---|
| `audit_tests.py` | Runs tests/test_*.py in parallel and names the ones set aside. | `python3 tools/audit_tests.py` · `python3 tools/audit_tests.py --changed`; imported by `daily_audit.py` |
| `checks.py` | Verify every mechanical rule in CODESTYLE.md and list what breaks them. | `python3 tools/checks.py` |
| `commit_apply.py` | Apply the night's commit proposal: per group `git add -- paths` + `git commit -- paths`, then one push. No model. | `python3 -m tools.commit_apply [date] [--dry-run] [--only N,M] [--no-push] [--force]` |
| `daily_audit.py` | The half of the daily audit a machine can do alone. Judgement stays with the /audit agent. | `python3 tools/daily_audit.py` |
| `depmap.py` | Generate docs/DEPENDENCIES.md from the imports actually present in the project's Python files. | `python3 tools/depmap.py` |
| `knowhowmap.py` | Regenerate each knowhow/<domain>/INDEX.md from its cards' q: lines, and check the cards. | `python3 tools/knowhowmap.py` |
| `knowhowq.py` | The q: rule of a knowhow card: one question, at most 120 characters, ending in '?'. | imported, not run |
| `knowhowrefs.py` | Knowhow check: a card's header must not cite a repo path that no longer exists. | imported, not run |
| `layering.py` | Layering check: which project package may import which, with today's violations as debt. | imported, not run |
| `manual.py` | Build the user manual as one PDF per workflow family, from the markdown in AlgoData. | `python3 tools/manual.py` |
| `projectmap.py` | Generate PROJECT_MAP.md from Graphify's graph: modules, who talks to whom, infra vs calculation, hot spots. | `python3 tools/projectmap.py` |
| `ratchet.py` | Ratchet: debt counts that may fall but never rise (CODESTYLE.md §8), baseline in ratchet.json. | `python3 tools/ratchet.py` |
| `readmetable.py` | Generate the «file» and «what it does» columns of every code folder's README table from the modules' docstrings. | `python3 tools/readmetable.py` |
| `skillmap.py` | Read every installed skill and rewrite docs/SKILLS.md: what exists, what it costs, where. | `python3 tools/skillmap.py` |
| `uiinventory.py` | Inventory every actionable widget of one zone of the window, drive each one, and say what happened. | `QT_QPA_PLATFORM=offscreen ALGO_DATA_ROOT=<test root> python3 tools/uiinventory.py --port 8771 --zone Portfolios [--write] [--shots DIR] [--out FILE.md] [--daemon-log FILE]` |
| `uiparts.py` | What a person can do to the widgets under one root: the inventory `uiinventory` drives. | imported, not run |
| `uiwalk.py` | Walk every zone of the window offscreen against a running daemon and report every exception. | `QT_QPA_PLATFORM=offscreen python3 tools/uiwalk.py --port P` |
| `vulture_whitelist.py` | Names vulture cannot see a caller for, and why each stays. | — |

`manual.py` renders the chapters to `docs/manual/NN-<family>.pdf` through headless Chrome, whose path lives in `config/machine.yaml`. The owner reads only PDFs (2026-09-26): the PDFs are in git and are the only thing in `docs/manual/`; the `.md` chapters and their `assets/` are the original and live in `AlgoData/manual-fuentes/`, out of the repo. `FAMILIES` decides which chapter goes in which PDF, and a chapter in no family stops the build. A family is rendered again only when its HTML or a picture it shows changed (`AlgoData/manual-fuentes/.rendered.json`; delete it to force a full rebuild) — `knowhow/eng/manual-pdf-rebuild-is-input-keyed.md`.

`daily_audit.py` writes `AlgoData/audit/YYYY-MM-DD-mechanical.md` (`core.paths.AUDIT`) and exits non-zero when something regressed.
It involves no model. **It is installed**, as the first half of `bin/nightly-audit.sh`, which cron
runs at 03:00 and which then runs the `auditor` agent headless on Sonnet for the judgement half.
`bin/nightly-docs.sh` runs the `documenter` the same way at 03:30, after waiting for the audit's
lock, and leaves its repairs uncommitted. `bin/nightly-fix.sh` runs the `fixer` on Sonnet at 04:00,
after the documenter, in the one checkout, and leaves its fixes uncommitted too — the owner commits
what he wants. `/sync` is not run unattended (it would commit on its own); cron runs `bin/nightly-commit-proposal.sh` at 05:45 instead, propose-only, and `commit_apply.py` applies it. Why the `claude` they call is found the way it
is: `knowhow/eng/headless-claude-from-cron.md`.

`sqx-lab/` is a vendored plugin, not project code: four skills that author custom blocks, random
groups, strategy templates and build projects. **Its path must not move** — `~/.claude/skills/sqx-*`
and `~/.claude/sqx_common.py` are symlinks into it, and `/sqx-setup` and `/sqx-doctor` name it
literally. `checks.py` and `depmap.py` skip it.

Run both tools after touching any Python:

```bash
python3 tools/depmap.py && python3 tools/checks.py
```
