---
name: autopilot
description: Run a project's whole workflow unattended — every SQX task and Python study from step 7 to 16, judging each judging step by criteria.yaml and cutting in SQX instead of stopping, cheap in tokens (reads only a status line and a short summary, never SQX's log). Use when the owner asks to run the workflow automatically, unattended, end to end, with the autopilot, or "sin pararse".
---

# /autopilot

`pipeline/autopilot/` does the work; this skill only launches it and reads its three small files.
**Do not read SQX's log, the study reports or the run's stdout** — that is what makes it cheap.

## 1. Before

- The project exists, built by `sqx.projects.builder --workflow` (step 5), and is not the master's.
- Hard rule 5: `python3 -m core.assets <SYMBOL>` — report the overrides; stop if non-zero.
- Hard rule 3: the worker is shared. `ListAgents`, `ls -lt <worker>/user/projects | head`. The
  autopilot refuses a worker that is up or held by someone else; never stop it to make room.
- Show the plan: `python3 -m pipeline.autopilot.run --project P --plan`. Tell the owner, in one
  line per action, what will run and where it stops. Say whether `dev.on` is true in
  `pipeline/autopilot/criteria.yaml` (a random draw of `dev.sample` at the steps in `dev.at`).

## 2. Run

```bash
python3 -m pipeline.autopilot.run --project P > /dev/null 2>&1
```

with `run_in_background: true`. You are woken when it exits. Meanwhile, if asked how it goes,
read only the newest `AlgoData/autopilot/<P>/*/estado.txt` (one line).

## 3. After

Read `AlgoData/autopilot/<P>/<stamp>/resumen.md`, and `fallo.md` only if it exists. Report to the
owner in Spanish: per step, what ran, how long, the cut (in → out, limbo count), and where it
stopped. On a failure, say the step and the reason from `fallo.md`; do not dig into logs unless
he asks.

A judge's numbers are in `paso-<n>/hechos.parquet`; to see which keys a rule can use:
`python3 -m pipeline.autopilot.facts --project P --step N --grep <text>`.

## Never

- Edit `criteria.yaml` without the owner: rules are his (hard rule 11 — an ambiguous rule is a
  question, not a default).
- Run it on a `Trade_` project while `dev.on` is true without saying so first: the draw deletes
  all but `dev.sample` strategies of the cut databank.
