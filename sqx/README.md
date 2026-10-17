# sqx — the surface over StrategyQuant X

[StrategyQuant X](https://strategyquant.com) (SQX) is a commercial GUI strategy builder: it generates trading
strategies by genetic search and then stress-tests them (out-of-sample retests, Walk-Forward Matrix, Monte
Carlo, parameter permutation). This project drives it **headless**, through its local HTTP `-project` API and
by writing its file formats directly — custom blocks, random groups, strategy templates, `project.cfx` and
`.sqx` archives — so that a whole research run is a command, not a sequence of clicks. Everything the rest of
the repo knows about SQX goes through this folder. The statistics that run on top of SQX's output live in
`studies/` and `engines/`, not here.

Rules for anyone (human or agent) editing here: [`CLAUDE.md`](CLAUDE.md). Facts about the formats and the API:
[`../knowhow/`](../knowhow/INDEX.md) (`sqx-format/`, `sqx-drive/`, `authoring/`, `export/`).

## Subfolders

| folder | what it does |
|---|---|
| `projects/` | The core. Builds a SQX project from a template (or none) plus an asset card, configures each workflow step's task (costs, windows, cross-checks, ranges), drives workflow stages, registers and retires projects. Reads/writes `project.cfx` |
| `templates/` | Authors a strategy template from one idea: puts a condition into a proven skeleton and records it in a template library |
| `blocks/` | Custom blocks into an install, the block taxonomy (every block the builder can draw, ~770 rows), and named palettes (`palettes/*.yaml`) that restrict a run to one idea family |
| `variants/` | The variant factory (robustness protocol, stage 2): a design brief in, N rewritten `.sqx` files plus a manifest out; loads them into a worker, retests, collects the metrics and per-day equity. Subfolders `design/` (which combinations) and `build/` (how a tuple becomes a file) |
| `structural/` | Rewrites a strategy's *logic* rather than its values: delete one entry condition (ablation) or flip the order direction (inversion). Workflow step 23 |
| `export/` | Gets data out of SQX into the data root: metrics, trades, Walk-Forward Matrix, parameter-permutation results, retests, bars, log archive. Nothing here writes into the repo |
| `curate/` | The only folder that changes what a databank holds: writes a verdict (keep/drop) and applies it inside SQX. Nothing runs without `--apply` |
| `inspect/` | Read-only tools: render a project as a Markdown pipeline map, check its health, read instruments and feeds, index `.sqx` files. Safe while SQX is running |
| `data/` | Runs the GUI's "Update all" data download on the master and reconciles `assets/_policy.yaml` with what SQX now holds |
| `views/` | The SQX "Export Data View" column set the exports read |
| `worker/` | `guard.py`: whether a worker is up, and the marker a launcher job leaves while the worker it started runs |
| `databank/` | `fingerprint.py`: a databank's strategies reduced to one signature, so an export can tell a resave from a change |
| `daylog.py` | Today's SQX log of an install, as the lines that say which project runs and how far. | imported | log → lines |
| `log.py` | SQX's own log from the moment of a launch on, across midnight: only the lines written since |
| `groups/` | Empty directory (no tracked files) |

Each folder with code has its own `README.md` listing its files, commands and inputs/outputs.

## How a run is made

Source of truth: rules 3, 10, 13, 14, 15 and 19 in [`../CLAUDE.md`](../CLAUDE.md).

- **Every run happens in a custom project**, never in SQX's stock `Builder`/`Retester`. `projects/builder.py`
  clones one from a frozen donor project, configured from `assets/<SYMBOL>.yaml` (costs, data windows).
  Names are `Test_…`, `Trade_…` or `Research_…`; each is recorded in a registry CSV in the data root.
- **One project holds the whole workflow.** With `--workflow`, one task is created per step (build, OOS
  retests, cross-checks, Monte Carlo, …), each with its own spread, slippage, swap and asset; only the step
  being run is switched on (`projects/stage.py`).
- **One direction per strategy** (long or short, never both); **at most 2 entry and 2 exit conditions**,
  counted per random hole; no time-of-day blocks and no stop/limit entry blocks. The builder refuses
  violations (`projects/buildrules.py`).
- **Three SQX installs**: the owner's master (GUI, port 5050), a short-job conductor (5060) and a
  one-long-job custodian (5070). Headless installs are started and stopped only through
  `bin/sqx-worker.sh`, which carries an owner lock. See `knowhow/sqx-drive/three-install-topology.md`.
- SQX deletes on-disk strategies that are not in memory on sync, so projects are snapshotted before any
  restart (rule 1, `knowhow/databanks/sync-deletes-unloaded-files.md`).

## Main commands

Run from the repo root. Whole-workflow runs go through `bin/workflow.sh` (see [`../bin/README.md`](../bin/README.md)).

| command | does |
|---|---|
| `python3 -m core.assets <SYMBOL>` | Cost/window preflight; required before authoring (rule 5) |
| `python3 -m sqx.projects.builder Test_<name> --purpose "…" --template <sqx> --symbol <SYM> --timeframe <TF> --workflow --role custodian` | Build a project (`--simple long\|short` instead of `--template` for no template) |
| `python3 -m sqx.projects.stage --cfx <cfx> --step <step>` | Switch on one step's task only |
| `python3 -m sqx.projects.retire --list` / `<P> --role custodian --yes` | List / retire projects |
| `python3 -m sqx.templates.build <name> <blocks.xml> <key> <out.sqx>` | Template from one condition |
| `python3 -m sqx.blocks.palette [NAME]` | Resolve a palette against the taxonomy |
| `python3 -m sqx.variants.make` | Build a variant batch from a design brief |
| `python3 -m sqx.structural.make` | Ablation / inversion variants |
| `python3 -m sqx.export.export_metrics --project P --databank D` | Metrics CSV per databank |
| `python3 -m sqx.inspect.dump_project <PROJECT>` | Markdown map of one project |
| `python3 -m sqx.curate.verdict --project P --databank D --keep "<pandas filter>"` | Write a verdict, then `apply_verdict.py --apply` |

## State

In daily use. Open work on this surface is tracked in the repo-root `OPEN.md`; the owner-facing manual
chapters (Spanish) are in `docs/manual/`.
