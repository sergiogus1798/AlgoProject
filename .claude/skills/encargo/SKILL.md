---
name: encargo
description: Write an encargo — one self-contained brief in docs/encargos/ that a single agent instance executes without reading anything else — in the house shape, numbered, registered in the folder's README, with the owner's decisions listed as questions. Use when the owner asks to write an encargo, a brief or a plan for another agent, to turn an idea or a dossier into work for later, or to split work across instances.
---

# /encargo

An encargo is what one instance needs for its part, and nothing more. It is dispatched with
«Lee `docs/encargos/NN-<nombre>.md` y ejecútalo entero». Spanish: the owner reads it.

1. **Number and overlap.** `ls docs/encargos | sort -n | tail -3` gives the next `NN`;
   `grep -n '<tema>' docs/encargos/README.md OPEN.md` shows whether one already covers it — then
   edit that one. `docs/AgentPDFs/WORKFLOW.md` rules where they disagree.
2. **Ask before writing** (rule 11): every point where the idea admits two readings is a question
   to the owner now, or — when only the executing agent can frame it — a line under «Decisiones
   del dueño». Never a default written into the brief.
3. **Write `docs/encargos/NN-<nombre>.md`** in this shape (copy the tone of a recent one, e.g.
   `sed -n 1,60p docs/encargos/42-*.md`):

   | section | holds |
   |---|---|
   | `Tu oficio` | who the agent is, in two lines, and its model: Sonnet for mechanical work, Opus for design, statistics or authoring (rule 17) |
   | `Tu encargo` | what to build and what it returns to the owner: a filter, a metric, a survivor list — a decision, not a description |
   | `§0 De dónde sale` | the owner's words with date, the dossier or `OPEN.md` § it comes from |
   | numbered parts | each with the files it owns, the exact commands, and the routes to read (`file:line`, never pasted content) |
   | `Decisiones del dueño — pregúntalas (regla 11)` | every open choice, with the readings spelled out |
   | `Lo que no tocas` | the master, other fronts' files, `oos2` unless the owner authorised it for this task |
   | `Objetivo — un comando` | ONE command that exits 0 only when the encargo is done, and non-zero while it is not: the test, the check, the study's own exit code (`python3 tools/depmap.py && python3 tools/checks.py && python3 -m pytest tests/test_<x>.py -q`). It is the brief's contract, written before the parts. An encargo whose done-ness cannot be a command (design, authoring, an idea) says so in this row and keeps `Verificación` instead |
   | `Cómo cierras` | qué hizo · qué verificó, con la salida pegada · qué dejó sin hacer y por qué · qué descubrió para `knowhow/` — the changed files and «¿Quieres hacer el commit?» |

   Several fronts in one encargo share no file. The shared ones follow the folder's protocol:
   `docs/DEPENDENCIES.md` is regenerated, never merged; `requirements.txt` only gains lines;
   `ledger/thresholds.yaml` gains rows at the end of its section, read as `ledger:<key>`. A new
   command carries its manual chapter in the same encargo (rule 8).
4. **Register it:** a row in `docs/encargos/README.md` under its batch (`fichero | qué construye |
   depende de`); a new batch gets a dated heading saying where it comes from.
5. **A plan that spans sessions** carries a state table and a log at the top, updated by each
   session (model: `41-fases-0-y-1.md`).
6. **Dispatch it as a loop when it has an `Objetivo — un comando`.** The last line of the encargo is
   the command that launches it:

   ```
   /loop Lee docs/encargos/NN-<nombre>.md y ejecútalo entero. Tras cada iteración corre el
   Objetivo; si sale 0, para el bucle; si no, arregla lo que falló y vuelve a correrlo.
   ```

   `/loop` without an interval self-paces: the agent iterates until the objective's command exits 0
   and stops the loop itself. Without that command there is no loop — a brief verified by eye is run
   once, by hand, as before.

**A fulfilled encargo is deleted**, not marked done: what it taught is in `knowhow/`, the manual
and the code; remove its README row and say where each part went.
