# tools — project maintenance

| file | what it does | run it |
|---|---|---|
| `checks.py` | Verify every mechanical rule in `CODESTYLE.md` and list what breaks them | `python3 tools/checks.py` |
| `depmap.py` | Read the real imports and regenerate `docs/DEPENDENCIES.md` | `python3 tools/depmap.py` |
| `manual.py` | Build the whole user manual as one PDF from the markdown pages in `docs/manual/` | `python3 tools/manual.py` |
| `daily_audit.py` | The half of the audit a machine can do alone: checks, tests, corrupt projects, missing manifests, undecided asset costs | `python3 tools/daily_audit.py` |

`manual.py` renders the markdown to `docs/manual/AlgoProject-Manual.pdf` through headless Chrome, whose path lives in `config/machine.yaml`. Neither the PDF nor the intermediate HTML is in git: both are products of the `.md` files, which are the original.

`daily_audit.py` writes `audit/YYYY-MM-DD-mechanical.md` and exits non-zero when something regressed.
It involves no model, so it can run unattended. Enable it with:

```bash
(crontab -l 2>/dev/null; echo "0 8 * * * cd ~/Desktop/AlgoProject && python3 tools/daily_audit.py") | crontab -
```

It is **not** installed. The judgement half — documentation drift, SQX health, statistical rigour —
needs `/audit`, which is run by hand because no `claude` CLI exists on this machine.

`sqx-lab/` is a vendored plugin, not project code: four skills that author custom blocks, random
groups, strategy templates and build projects. **Its path must not move** — `~/.claude/skills/sqx-*`
and `~/.claude/sqx_common.py` are symlinks into it, and `/sqx-setup` and `/sqx-doctor` name it
literally. `checks.py` and `depmap.py` skip it.

Run both tools after touching any Python:

```bash
python3 tools/depmap.py && python3 tools/checks.py
```
