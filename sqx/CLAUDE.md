# sqx — the SQX surface

Everything that reads, drives or authors StrategyQuant X. Read `knowhow/03-driving-sqx.md` before
writing anything that talks to SQX, and `knowhow/04-export.md` before touching an export.

## Before authoring anything

```bash
python3 -m core.assets <SYMBOL>      # blocking. Non-zero exit means stop and ask
```

Then say out loud which spread, commission and swap you are applying and where they differ from what
SQX carries. `sqx/inspect/instruments.py` shows what SQX carries today.

## Lanes — one owner each, because this state is shared and not reversible

| lane | who | rule |
|---|---|---|
| SQX lifecycle (start/stop), master install | one session only | announce before stopping SQX |
| builds and long jobs | **custodian** `SQX_w2` / 5070 | 48 cores, 48 g. One job at a time, no command between start and collect. **Never on the master** |
| authoring blocks, groups, templates, projects | **conductor** `SQX_w1` / 5060 | 8 cores, always awake. Start it for the job, then `bin/sqx-worker.sh stop` |
| reading configs, `.cfx`, task chains | anyone | read-only, never triggers a restart |
| snapshots and recovery | one session | snapshot before anything destructive |
| repairing a project on disk | SQX-lifecycle lane | `repair/` refuses to run while a process holds the install |

If you were not told you own the lifecycle lane, you do not. Read freely; change nothing that needs
SQX to restart.

## What lives here

`inspect/` read-only tools · `repair/` writes to a project on disk, guarded, only with SQX closed ·
`variants/` the variant factory: a design brief in, a batch of `.sqx` and its manifest out, touching no SQX ·
`export/` the three exports plus the log archiver · `projects/` authored `.cfx` for GUI import ·
`templates/`, `blocks/`, `groups/` authoring sources · `views/` `.vw` definitions.

Two checks worth running before trusting a project: `inspect/project_health.py` (broken task
references, version drift, mangled fields) and `inspect/template_check.py` (whether the strategies a
project built actually carry the blocks its template fixes — on this install, they do not).

Authoring skills (`sqx-custom-block`, `sqx-random-group`, `sqx-strategy-template`,
`sqx-strategy-project`) are installed globally and live in `tools/sqx-lab/`. A project the skill
builds on the worker is invisible on the master: hand it over as a `.cfx` for GUI import, and say so.
