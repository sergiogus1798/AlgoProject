---
name: new-study
description: Add a study to studies/ complete in one pass — the module in the contract's shape, its rows in the window's catalogue, its thresholds in the ledger, its perf target, its test, its manual chapter and the closing checks. Use when the owner asks for a new study, analysis, reading, test or screen over a strategy or a population, or when an encargo builds one.
---

# /new-study

A study is registered in seven places; each one forgotten is a later session's audit finding.

**Before any code** (rule 11): what decision the study ends in — a filter for generation, a screen
with its cost in strategies next to its gain, the metric to optimise, or a survivor list — on which
sample (random-entry nulls and PSR only on OOS, never `oos2` without the owner's word), and which
family and workflow step. Unclear → ask. Then read `CODESTYLE.md`, `studies/CLAUDE.md` and
`core/study/CONTRACT.md` (delegate the contract's 178 lines if you only need one block kind).

1. **Does it exist?** `graphify query "<the question>" --budget 800` and the family table in
   `studies/CLAUDE.md`. A new angle on an existing study is a knob there, not a folder.
2. **The module**, `studies/<family>/<study>/`:
   `config.yaml` (every knob, commented) · `tooltips.py` (one Spanish sentence per knob) ·
   `one.py` `run(strategy, inputs, cfg) -> dict` · `many.py` `run(inputs, cfg) -> dict` when it
   judges a population · `report.py` (the command: prints, writes, writes `verdict.csv`) ·
   `README.md`. Compute through `engines/`, never import another study, return the contract's
   dict, print `PROGRESS <0..100> <state>` lines, write under
   `reports/<P>/<D>/<day>/<study>/` with a manifest naming the input judged.
3. **Thresholds** go to the end of the study's section of `ledger/thresholds.yaml`, read as
   `ledger:<key>` — picked values are the owner's; record the search space they came from.
4. **The window:** one row each in `catalogue.STUDIES`, `catalogue.ROLE` and `knobs.LOADERS`
   (`ui/daemon/results/README.md` §Contracts), and what `ui/README.md` lists for a runnable
   study (`ui/daemon/runner/`, `ui/daemon/databank/layout.py`). Check with `/ui-shot`.
5. **Perf target** in `perf/inputs/targets.py` when it reads a population or simulates.
6. **Test:** `tests/test_<study>.py`, a known-answer case — an input whose verdict you can state
   by hand.
7. **Docs:** the study's row in `studies/CLAUDE.md`'s family table, the manual chapter with
   `/manual-chapter` (rule 8), a card for any non-obvious fact (`/doc`), and — if it fills a
   workflow step — its row in `docs/AgentPDFs/WORKFLOW.md`.
8. **Close:**

   ```bash
   python3 -m pytest tests/test_<study>.py -q
   python3 tools/depmap.py && python3 tools/checks.py
   ```

Report the result as the decision it supports, the files changed, and «¿Quieres hacer el commit?».
