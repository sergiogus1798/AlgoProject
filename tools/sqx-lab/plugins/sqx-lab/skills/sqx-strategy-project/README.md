# sqx-strategy-project

A portable Claude Code skill that turns a set of StrategyQuant X strategy templates into a
runnable **build project** (`project.cfx`) — by **cloning an existing project** on the target
install and wiring each template in as its own build task.

Fourth in the SQX authoring suite:

| Skill | Builds |
|---|---|
| `sqx-custom-block` | atomic trading rules (custom blocks) |
| `sqx-random-group` | the pools the builder samples |
| `sqx-strategy-template` | full strategies (`.sqx` templates) |
| **`sqx-strategy-project`** | **the build project that runs those templates as tasks** |

## What it does

A `project.cfx` is a ZIP of `config.xml` + one ~3 MB `Build-Task{N}.xml` per build task. Each task
embeds its full build configuration; the strategy it builds is a single attribute
(`<StrategyType templateFile=>`). So "a project that builds N templates with identical settings" =
**clone one donor task N times, swapping only the template + its output databank** (+ optionally the
AvgTradesPerMonth gate and the per-task time cap). Data feed, symbol, timeframe, and the exit/acceptance
stack are inherited from the donor unchanged.

The engine is **install-parametric** (install + base project + templates are inputs) and
**base-derived** (the project tag, version, system databanks, and inactive tasks come from the base,
not from code). Every task it emits is byte-identical to `donor + exactly the four swaps`.

## Use it

1. `python engine/discover.py "<SQX install folder>"` → `catalog.json` (clonable projects + template sets).
2. Pick a base project + a template set.
3. `engine.generate.make_project(...)` → emits a verified `project.cfx` to `engine/out/`.
4. `engine.generate.deploy(...)` → places it into the install (**SQX must be closed**).
5. Open SQX, run a Build to confirm.

See `examples/gen_project_example.py` for a copyable batch and `SKILL.md` for the full workflow.

## Files

- `SKILL.md` — the workflow (read first).
- `engine/discover.py` — install → `catalog.json`.
- `engine/generate.py` — `make_project` (clone + wire + self-verify) · `deploy` (install placement).
- `reference/project-grammar.md` — what a `project.cfx` IS (the ZIP model, the four holes, the gotchas).
- `examples/gen_project_example.py` — base + templates → `project.cfx`.
- `evals/run_evals.py` — deterministic structure self-test (11 cases: faithful-clone + guardrails).
- `catalog.json` — per-install, gitignored.

## Status

The engine reproduces the **build-confirmed** task-wiring mechanic (`_attach_breakout_fleet.py` +
`_build_long_project.py`) byte-faithfully and passes the structure evals (11/11). A user build-confirm
of an *engine-generated* project in AlgoWizard is the final proof — pending.

## Requirements

Python 3.8+ (standard library only). A StrategyQuant X **build-144** install.
