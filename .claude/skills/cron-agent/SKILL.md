---
name: cron-agent
description: Add an unattended agent that runs from cron — its agent file, its bin/ script with lock, dry-run and headless `claude -p` on Sonnet, a crontab minute no other job uses, its report folder and its manual chapter. Use when the owner asks for a new nightly, daily or weekly agent, to automate a recurring task, or to schedule something to run by itself.
---

# /cron-agent

Nine of these exist (`ls bin/*.sh`); each was assembled from the previous one. Read the two cards
first — their headers only: `knowhow/eng/headless-claude-from-cron.md` and
`knowhow/eng/cron-schedule-no-shared-minute.md` (it holds the current chain of times).

**Ask first** (rule 11): when it runs, what it may write, and what it must never do (buy, log in,
commit, touch SQX). An agent that starts or queries an install needs the owner's explicit word.

1. **The agent**, `.claude/agents/<name>.md` (copy the frontmatter of `dealHunter.md`): a
   `description` saying when it runs and what it never does, the narrowest `tools`, `model:
   sonnet` unless its work is design or statistics (rule 17). It works in the one checkout, never
   commits (rule 12), never asks — nobody answers at night — and ends with a short Spanish summary.
2. **The script**, `bin/<cadence>-<name>.sh`, copied from `bin/daily-funding-deals.sh`. Keep:
   - `DATA` from `core.paths`; log and lock in `$DATA/logs/`; `flock -n 9` and skip if held;
   - the `claude` binary looked up each run (`sort -V | tail -1`), never hardcoded;
   - `--dry-run` that prints the resolved paths and runs nothing;
   - `timeout <N>m "$CLAUDE" -p --agent <name> --model sonnet --add-dir "$DATA"
     --allowedTools=<list>` — headless ignores `settings.json`, so every tool and every directory
     outside the repo is passed here; deny what must never happen with `--disallowedTools`;
   - the deterministic Python around the agent runs even when the agent cannot.
   Whatever a script can do without a model is a `python3 -m` step, not a prompt.
3. **Reports** go to `AlgoData/audit/<name>/` (`core.paths.AUDIT`), never into the repo.
4. **Try it:** `bin/<script>.sh --dry-run`, then one real run by hand; read only the tail of its log.
5. **Schedule it:**

   ```bash
   crontab -l > ~/Desktop/AlgoData/logs/crontab-backup-$(date +%F).txt
   crontab -l | grep -v '^#' | grep . | awk '{print $1,$2,$5}' | sort | uniq -d   # must print nothing after the edit
   ```

   Pick a minute no entry uses; a script that waits on another's lock starts **after** it
   (`flock -w` only waits on a lock already held). Show the owner the new line before installing it.
6. **Record:** update the chain in `cron-schedule-no-shared-minute.md`, the agent's line where
   CLAUDE.md's router names its domain, the manual chapter (`/manual-chapter`), then
   `python3 tools/checks.py`.
