---
name: audit
description: Run the daily project audit — documentation against reality, code and data integrity, statistical rigour, and the three SQX failures that count (broken exports, oversized logs, corrupt blocks). Use when the owner asks for an audit, a health check, or what is broken.
---

# /audit

Launch the `auditor` subagent. It is read-only and writes `audit/YYYY-MM-DD.md`.

1. Check whether today's report already exists in `audit/`. If it does, ask whether to re-run or read it.
2. Spawn the agent with the `auditor` subagent type, in the background.
3. When it returns, give the owner the three findings that matter, in Spanish, with severity. Do not
   paste the whole report; name the file.

Pass an area name as an argument (`docs`, `sqx`, `code`, `stats`) to audit only that area. With no
argument it does all four.

The auditor never starts or stops SQX and never fixes what it finds. Fixing is a separate decision,
and it is the owner's. `sqx` means only the export path, log sizes and corrupt blocks or archives —
how a project is configured is the owner's choice and is never audited unless he asks for it.

## The mechanical half runs without a model

```bash
python3 tools/daily_audit.py
```

Rule checks, tests, projects that fail to render, exports missing a manifest, and assets a live
project uses whose real cost is still undecided. It writes `audit/YYYY-MM-DD-mechanical.md` and exits
non-zero on a regression, so it can sit in cron unattended — `tools/README.md` has the line. Read its
report first; the agent should spend its effort on what a script cannot see.
