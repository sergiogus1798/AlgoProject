---
name: audit
description: Run the daily project audit — documentation against reality, SQX health, code and data integrity, statistical rigour. Use when the owner asks for an audit, a health check, or what is broken.
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
and it is the owner's.
