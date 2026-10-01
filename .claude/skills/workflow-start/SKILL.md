---
name: workflow-start
description: Start a new workflow run from nothing — the three expert agents for the idea, the template and the building blocks (spending what they need), then the custom project, the palette written into its Build task, and the autopilot from step 6 on. Use when the owner asks for a new strategy run, a new idea on a symbol, or a complete workflow from scratch.
---

# /workflow-start

Steps 1-6 decide what everything after them is spent on (owner, 2026-10-01: «me da igual que esos
pasos consuman más tokens que el resto del workflow junto»). They go to three specialists; the rest
goes to the autopilot, which is cheap.

## 1. Idea — `ideaExpert`

Agent `ideaExpert` (or a general-purpose agent told to follow `.claude/agents/ideaExpert.md`, model
opus) with the symbol, the owner's hint if any, and what was tried. It writes
`AlgoData/ideas/<SYMBOL>/<date>-<slug>.md`. Show the owner its three ideas, one line each, and its
recommendation, and **ask which one** — with any ambiguity it returned (hard rule 11). Never pick
for him unless he says «elige tú».

## 2-3. Template — `templateArchitect`

With the idea file and the chosen idea. It authors and installs what is missing on both workers and
files the template in the library, verified block by block. Relay its verification table.

## 4-5. Preflight and project

`python3 -m core.assets <SYMBOL>` (stop on non-zero). Check the custodian is free (`ListAgents`,
`ls -lt <worker>/user/projects | head`, the OWNER lock). Then:

```bash
python3 -m sqx.projects.builder Test_<SYMBOL>_<template>_<TF> --purpose "<why>" \
    --template AlgoData/templates/library/<template>/template.sqx --symbol <SYMBOL> \
    --role custodian --timeframe <TF> --workflow
```

## 6. Building blocks — `buildingBlocksExpert`

With the idea, the template and the project. It writes `sqx/blocks/palettes/<template>.yaml` and
applies it: `python3 -m sqx.projects.buildingblocks --project P --palette <template> --role custodian`.
The conditions on must be inside the owner's band (90-170).

## 7. The rest — `/autopilot`

From the build (step 6's task) to 16.5, unattended, reading only `resumen.md`.

## Never

Skip the owner's choice of idea; let one expert do another's step; build on the master.
