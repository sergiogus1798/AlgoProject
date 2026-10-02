---
name: research-direct
description: Ask the research director where to investigate next — refresh the results memory, print the board of cells (asset × timeframe × direction × family) the owner's prior rates Alta or the market profile's measurements admit, run the researchDirector agent to pick one cell and bring three ideas with their block palettes, and show the proposal. Costs 10-30 $ per proposal; launches nothing in SQX. Use when the owner asks what to investigate next, for a research proposal, "qué investigo ahora", or presses «Proponer investigación».
---

# /research-direct

The director decides **where** (which cell) and **what** (three ideas, each with its palette);
`/workflow-start`'s chain builds them afterwards, from the window's «Investigar» panel, after the
owner's veto. Nothing here touches SQX. Design:
`docs/AgentPDFs/director-de-investigacion-2026-10-01.md` §6.

## 1. Refresh the memory (0 tokens)

```bash
python3 -m studies.research.memory.report
```

The profile is not refreshed here (20 min, 4 cores): if `AlgoData/research/profiles/run.json` is
older than the feeds, say so in one line and carry on — the owner decides when to re-measure
(`python3 -m studies.research.marketProfile.report`).

## 2. Print the board (0 tokens)

```bash
python3 -m studies.research.board
```

Show the page to the owner as printed. No cell on it → stop: «ninguna celda entra en el
tablero». Do not offer a cell from outside the board. The gate since 2026-10-02 (owner): the prior
rates the cell Alta, or it passes the four filters, or a sweep variant passes on a plateau — the
earlier «grey cells do not enter» is superseded.

## 3. Run the director

Agent `researchDirector` (or a general-purpose agent told to follow
`.claude/agents/researchDirector.md`, model opus). It launches the `ideaExpert` itself. A
proposal costs 10-30 $: when the owner did not ask for one explicitly, ask before this step.

## 4. Show the proposal

The agent ends with `PROPUESTA: <path>.json`. Show the owner the `.md` beside it: the diagnosis,
the three ideas one short block each (rule, quarry, palette, custom blocks, custodian hours, how
it can fail), «ya van K ideas», the two standing costs, and the provisional-costs warning when it
is there.

**Ambiguity is a stop with a question (hard rule 11).** Every idea with `questions` is shown as
the question and its readings, and the owner is asked which. Write his answer into the proposal:

```python
from ui.daemon.research import proposals
proposals.answer("<id>", "<idea name>", 0, "<the reading he chose>")
```

Never choose for him, and never rewrite the idea's rule yourself.

## 5. What comes next — the owner's, not this skill's

The owner vetoes and launches from the window (BIBLIOTECA › Investigar › Propuesta › «Crear
plantillas y lanzar en SQX»): one idea after another on the custodian. This skill never launches.

## Never

Run the director twice for the same press; start a worker, a build or the autopilot; edit
`assets/`, a template or a palette; propose on a cell that is not on the board.
