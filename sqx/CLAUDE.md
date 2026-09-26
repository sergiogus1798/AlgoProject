# sqx — the SQX surface

Everything that reads, drives or authors StrategyQuant X. Read `knowhow/sqx-drive/` before
writing anything that talks to SQX, and `knowhow/export/` before touching an export.

## Before authoring anything

```bash
python3 -m core.assets <SYMBOL>      # blocking. Non-zero exit means stop and ask
```

Then say out loud which spread, commission and swap you are applying and where they differ from what
SQX carries. `sqx/inspect/instruments.py` shows what SQX carries today.

## Every run gets its own custom project

Owner, 2026-09-23, hard rule 10. Never run anything in the stock `Builder` or `Retester`, and never
treat one as a scratch harness — the knowhow pages that used `Retester` that way predate this rule.
One command builds the project:

```bash
python3 -m sqx.projects.builder <name> --template <lib>/template.sqx --symbol <SYM> \
    --role custodian --timeframe <TF> --workflow
```

It clones the frozen donor and prices each task from `assets/` by its own segment. With
`--workflow` (owner, 2026-09-25) the one project holds **every step's task** — the donor's, plus
`CrossTF` and the three WFC legs — with only Build and OOS switched on. Each later step's
configurator (`crossmarket`, `crosstf`, `mcretest`, `spp`, `wfc`, `wfm`) writes its task and leaves
only its own step active, because `action=start` runs every active task and skips the rest; by
hand it is `python3 -m sqx.projects.stage --cfx <cfx> --step <step>`. Without `--workflow`,
`--tasks`/`--only` keep a subset, for a study run on its own. A stock project is never borrowed.

## Lanes — one owner each, because this state is shared and not reversible

| lane | who | rule |
|---|---|---|
| SQX lifecycle (start/stop), master install | one session only | announce before stopping SQX |
| builds and long jobs | **custodian** `SQX_w2` / 5070 | One job at a time; between start and collect only `-project action=status`, never `count`. **Never on the master** |
| authoring blocks, groups, templates, projects | **conductor** `SQX_w1` / 5060 | 8 cores, always awake. Start it for the job, then `bin/sqx-worker.sh stop` |
| reading configs, `.cfx`, task chains | anyone | read-only, never triggers a restart |
| snapshots and recovery | one session | snapshot before anything destructive |
| repairing a project on disk | SQX-lifecycle lane | `repair/` refuses to run while a process holds the install |

If you were not told you own the lifecycle lane, you do not. Read freely; change nothing that needs
SQX to restart.

## What lives here

`inspect/` read-only tools · `repair/` writes to a project on disk, guarded, only with SQX closed ·
`variants/` the variant factory: a design brief in, a batch of `.sqx` and its manifest out, touching no SQX ·
`structural/` rewrites a strategy's logic — one condition ablated, or the direction inverted — for step 23 ·
`export/` the three exports plus the log archiver · `projects/` authored `.cfx` for GUI import ·
`templates/`, `blocks/`, `groups/` authoring sources · `views/` `.vw` definitions.

Two checks worth running before trusting a project: `inspect/project_health.py` (broken task
references, version drift, mangled fields) and `inspect/template_check.py` (whether the strategies a
project built actually carry the blocks its template fixes — on this install, they do not).

Authoring skills (`sqx-custom-block`, `sqx-random-group`, `sqx-strategy-template`) are installed
globally and live in `tools/sqx-lab/`; the installer puts this project's rules on top of each
(`tools/sqx-lab/overlays/`) and no longer wires `sqx-strategy-project` (retired 2026-09-25, against
hard rule 10). `sqx-strategy-template` is THE template skill — the old `/strategy-template` is gone. **They are installed by
hand, not by `/plugin`** — that command does not exist in this environment (2026-09-24). One script
does the whole wiring and is idempotent: `bin/sqx-lab-install.sh`, manual page `40-sqx-lab.md`. Run
it after updating the toolkit and whenever the install's blocks or groups change: a **stale catalog
does not fail, it invents atoms** the building install does not have, and the template is then
silently wrong. `/sqx-doctor` says whether it is stale, and on 2026-09-24 it was — twenty days old
and built against the master instead of the conductor. A project the skill
builds on the worker is invisible on the master: hand it over as a `.cfx` for GUI import, and say so.
