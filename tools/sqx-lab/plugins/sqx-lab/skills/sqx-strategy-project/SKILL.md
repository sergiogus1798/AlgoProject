---
name: sqx-strategy-project
description: Create a StrategyQuant X / AlgoWizard build PROJECT (project.cfx) by cloning an existing project on THIS install and wiring a chosen set of strategy templates as N build tasks — each task its own output databank plus optional acceptance / time-cap settings. Inherits the donor project's data feed, symbol, timeframe, and exit/acceptance settings unchanged; only the strategy template + output databank (+ those two settings) vary per task. Install-bound and clone-based — never hand-builds a project from scratch. Fourth in the suite after sqx-custom-block, sqx-random-group, sqx-strategy-template. Use when the user asks to create / set up / build / wire a build project, a builder project, a strategy fleet project, or "turn these templates into a project / tasks".
allowed-tools: Bash(python:*), Bash(py:*), Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# sqx-strategy-project — clone a project + wire templates into build tasks

Turn a set of strategy templates — the `.sqx` files the `sqx-strategy-template` skill emits —
into a runnable AlgoWizard **build project** (`project.cfx`), by **cloning an existing project on
this install** and replacing its build tasks with one task per template. Last in the suite:
`sqx-custom-block` builds the rules, `sqx-random-group` pools them, `sqx-strategy-template` wires
pools into templates, **this skill wires templates into a buildable project.**

How it works: `discover.py` reads the install → a catalog of **clonable base projects** and
**wirable template sets**; you pick a base + a template list; `generate.py` clones the base's
build task (bytes-level), swaps in each template + its own output databank, regenerates `config.xml`,
and **self-verifies**; then it's deployed into the install (SQX closed) and **build-confirmed**.

**Prerequisite:** Python 3.8+ (standard library only). A StrategyQuant X **build-144** install.

> **Run from the skill folder.** The `python engine/…` commands below use paths relative to
> **this skill's own directory** (where this `SKILL.md` lives) — run them from there.

---

## The one idea (read once)

A `project.cfx` is a **ZIP**: `config.xml` + one `Build-Task{N}.xml` per build task (each EMBEDS
~3 MB of that task's full build settings — data feed, symbol, timeframe, the whole exit + acceptance
stack) + two inactive helper tasks. **A build task's strategy template is one attribute** inside its
task XML (`<StrategyType templateFile="…sqx">`). So a project that runs N templates with identical
settings = **clone ONE donor task N times, swapping only the template + its output databank**.

This skill does NOT hand-author a project from scratch — too much of what makes a project *build*
(the 3 MB of embedded settings, the data binding, the acceptance protocol) lives outside anything
worth regenerating. It **clones a proven project and varies only the per-task holes**, staying inside
build-confirmed territory. Full model: `reference/project-grammar.md`.

### What varies per task (the only holes)

| Hole | Where it lives | Required |
|---|---|---|
| `templateFile` | `<StrategyType templateFile=>` in the task XML | ✅ the strategy to build |
| output databank | `<Databank label="Output databank" name="Output" value=>` in the task XML | ✅ where results save (UNIQUE per task) |
| AvgTradesPerMonth | acceptance condition in the task XML — the engine also forces the enclosing `<Condition>` to `use="true"` (donors ship it disabled; a number in a disabled condition gates nothing) and notes that in the report | ⬜ optional override |
| time cap | `<StopCondition minutes=>` in the task XML — the engine also sets `type="time-limit"` (the donor's `databank-full` type ignores `minutes=`) and notes it in the report | ⬜ optional override |

The exit stack and the other acceptance conditions are **inherited from the donor task unchanged.**

### Project-level OVERRIDES — instrument · timeframe · dates · trading options (optional)

Beyond the 4 per-task holes, `make_project(..., overrides=…)` can promote four donor-inherited
fields into **settable, project-wide** values (applied to every cloned task). Omit any block to
inherit the donor's value (backward compatible).

| Override | Sets | Engine fn |
|---|---|---|
| `instrument` | symbol (data key) + instrument id (+ optional timeframe); blanks `uSymbol` so SQX re-resolves the underlying | `set_instrument` |
| `timeframe` | retime every data `<Chart>` **without** switching instrument (SQX resamples from the M1 base) — pass at top level *instead of* `instrument` | `set_timeframe` |
| `dates` | the **IS backtest window** on the `<Data><Setups>` setup + the epoch data range | `set_dates` |
| `trading` | `spread`, `slippage`, `session`, `market_side`, `time_range` (the builder task's **"Limit time range"** intraday window), and `friday_exit` | `set_trading_options` |
| `generation` | `databank_cap` + `acceptance` — what the build KEEPS (see below) | `set_databank_cap` · `set_acceptance` |

```python
report = make_project(BASE, "NAME", tasks, out_cfx, overrides={
    "instrument": {"symbol": "EURUSD_M1_dukascopy", "instrument_id": "EURUSD_dukascopy", "timeframe": "H1"},
    "dates":      {"from": "2012-01-01", "to": "2020-12-31"},
    "trading":    {"spread": "3", "market_side": "long",
                   "time_range": {"from": "08:00", "to": "20:00", "exit_at_end": True}},
})
# Retime a duplicate WITHOUT switching instrument — pass "timeframe" at top level instead of "instrument":
#   overrides={"timeframe": "M30", "dates": {"from": "2012-01-01", "to": "2020-12-31"}}
```

**Instrument switch is a STRING swap — SQX heals the money metadata itself.** Build-confirmed
(2026-07-11): swapping the symbol + instrument id and loading the project makes SQX re-resolve
tickSize / pointValue / swap / commissions from its data manager (probe: stale index values →
correct EURUSD FX values on load). So `set_instrument` only rewrites the symbol/instrument
strings; it never fabricates tick economics.

**Gotcha — the `uSymbol` resolver (build-confirmed fix, 2026-07-11).** The data `<Symbol>`
element carries `uSymbol`/`uSymbolName`, SQX's *underlying-instrument resolver key* — and it is
the field the loader actually binds against, NOT `symbol`/`instrument` (a donor can carry a
display alias like `NQ_M1_dukas` yet resolve via `uSymbol="USATECHIDXUSD"`). If a switch leaves
`uSymbol` at the donor's underlying, the project loads with **"unresolved resources."**
`set_instrument` now **blanks `uSymbol`/`uSymbolName`** — SQX fills the correct underlying on load
(probe: `uSymbol=""` → SQX healed it to `XAUUSD` and resolved gold economics tickSize=0.001/
pointValue=100). Pass `usymbol=`/`usymbol_name=` only if a donor/source ever needs them explicit.
**CAVEAT (corrected 2026-07-13): blank `uSymbol` resolves ONLY under headless `sqcli saveconfig`.
The GUI still flags a blank-uSymbol project as "unresolved resources" and makes the user fix it by
hand.** So a raw deploy is headless-clean but GUI-dirty. The heal step: after deploying, run
`sqcli saveconfig` and copy the RESOLVED cfx it writes back over the deployed `project.cfx` —
the underlying is now filled in and the GUI opens it clean. Do this as the final step of any
deploy. Get valid `symbol`/`instrument_id` pairs from
`sqcli -symbol action=list` (columns 1 and 2). What SQX does NOT heal, so `overrides` sets it
explicitly: `<Chart spread>` and the epoch `<Symbol>` range. `set_dates` touches ONLY the
`<Data><Setups>` setup — never the disabled inverted cross-check retest setup.

**`generation` — what the build KEEPS (survivorship control).** Two knobs that decide which
strategies land in the output databank. They matter whenever you want an *honest* population
rather than a curated one — e.g. building a gate matrix, or measuring how often an edge fails.

```python
overrides={"generation": {
    "databank_cap": 20000,               # <Rankings><MaxStrategies> — donor caps at 1000
    "acceptance":   ["AvgTradesPerMonth"],  # keep ONLY these acceptance columns
}}
```
- **`databank_cap`** raises the databank size cap. The donor's 1000 means the build **trims to
  the best-1000 by fitness = survivorship bias**. Set it ≥ your generation budget so every
  strategy that passes acceptance is retained.
- **`acceptance`** ENABLES the keep-classes (`use="true"` — even when the donor ships them
  disabled, which the real donors do) and switches off every *other* condition in
  `<Rankings><Conditions>`. The default `["AvgTradesPerMonth"]` keeps a *measurability* floor
  (enough trades to form a returns series) and drops the *performance* filters (ProfitFactor /
  NetProfit / …), so the databank keeps winners **and** losers. It raises only if a keep-class
  doesn't exist in the donor at all. Only `<Rankings>` is touched — the CrossCheck
  acceptance blocks (WF / MonteCarlo / Retest) are left alone.

**`trading.friday_exit`** — the task's "Exit on Friday" option (close positions before the
weekend): `{"friday_exit": {"enabled": True, "exit_time": "20:00"}}`. Stored as seconds-of-day;
omit `exit_time` to flip the flag and keep the donor's time.

**`analysis_tasks` — adding a CustomAnalysis export step.** `make_project(..., analysis_tasks=[…])`
appends non-Build `CustomAnalysis` tasks that post-process a databank. Unlike a build task (a
3 MB donor clone) these are tiny and built from scratch:

```python
from engine.generate import build_analysis_task
analysis = [build_analysis_task("ExportReturnsMatrix",
                                input_args=r"C:\out\returns;daily",
                                input_db="BS-MyFleet",
                                slot="FullDatabank1")]     # or PerStrategy1/2
make_project(BASE, "NAME", tasks, out_cfx, analysis_tasks=analysis)
```
Slot choice follows the method's registration: `FullDatabank1/2` for whole-databank methods
(`ExportReturnsMatrix` is `TYPE_PROCESS_DATABANK`), `PerStrategy1/2` for per-strategy methods.
Non-destructive by default (output databank = input, `RemoveFailedStrategies=false`).

**The "Limit time range" trading option (`trading.time_range`).** The per-builder-task
`BuildTradingOptions` intraday window — **not** a named session and **not** a strategy block. Set
it with `trading.time_range = {"from": "08:00", "to": "20:00", "exit_at_end": true, "order_type_to_exit": 0}`:
the engine flips `LimitTimeRange=true` and writes `SignalTimeRangeFrom`/`To` (stored as
seconds-of-day; inputs accept `HH:MM` or raw seconds). `exit_at_end` toggles `ExitAtEndOfRange`;
`order_type_to_exit` is the GUI's **"Order types to close"** (All / Live / Pending) as an int enum —
donor default `0`, so **confirm the `0/1/2` → All/Live/Pending mapping in the GUI before relying on a
non-default value**. Omit `time_range` to leave the donor's window untouched.

### The load-bearing gotchas (the engine enforces these — don't fight them)

- **The output databank lives INSIDE the task XML**, not in `config.xml`. `config.xml`'s `<Task title=>`
  is a display label only. Clone without rewriting the internal `name="Output"` value and **every task
  writes to the donor's databank** — they collide. The engine swaps it per task and verifies it.
- **`templateFile` paths are ABSOLUTE** (build-144 has no relative form). They're resolved against the
  **target install**, so put the templates inside the install (`user/settings/StrategyTemplates/…`)
  and the project is self-contained on that machine.
- **SQX MUST be closed** when deploying — it rewrites `project.cfx` on close and will clobber the edits.

---

## Step 0 — One-time setup: ASK FOR THE SQX INSTALL FOLDER (mandatory)

> **`/sqx-setup` does this step for all four skills at once**; `/sqx-doctor` reports health.

**Shared install path — check first.** All four sqx-lab skills share one stored SQX folder:
`~/.sqx-lab/sqx-install.txt` (override the directory with `SQX_LAB_HOME`) — outside the plugin
folder, so a plugin update doesn't wipe it. Written automatically after the first successful
bootstrap of *any* sqx-lab skill. If it exists, `python engine/discover.py` with **no argument**
uses it — tell the user which folder is being used and only re-ask if they say it's wrong (then
re-run with the corrected folder, which updates the stored path). A path is stored only after it
validates as a real SQX install — and `discover.py` now refuses a non-install outright instead
of reporting "0 projects" as if that were success.

Otherwise: there are usually several SQX installs on one machine. **You MUST ask the user which
install** — the top-level folder (with `internal/` and `user/`), e.g. `C:\StrategyQuantX`.
Do not auto-pick. Then:

```
python engine/discover.py "<the folder the user gave>"
```

This writes `catalog.json` next to the engine and prints:
- **BASE PROJECTS (clonable)** — each project's name, folder, version, #build tasks, sample symbol/TF.
  A good base = one whose donor task already has the data/symbol/TF/exit settings you want; its build
  tasks are **template** tasks (so the `templateFile` hole exists).
- **TEMPLATE SETS (wirable)** — the `.sqx` under `user/settings/StrategyTemplates/`, grouped by subdir.
- **SETTINGS PRESETS** — the task-settings `.cfx` referenced (carried over unchanged).

`catalog.json` is your source of truth. Never invent a project or template name. (Need a template that
isn't there? Build it with `sqx-strategy-template` first. Need a base with different data? The user
must create that project in SQX once — this skill clones, it does not define data feeds.)

## Step 1 — Pick the base + the templates

From the catalog, choose:
- **base project** (`folder` + `path`) — its donor build task is the settings/data donor.
- **which templates** to wire — usually a whole template set (e.g. all of `breakout_fleet`), or a
  subset. Each becomes one build task.

State the plan in plain English — "clone `FX_ID_60_MKT_NEW` (EURUSD, 24 breakout tasks as donor),
wire all 24 `breakout_fleet_long` templates, each its own `BS-<stem>` databank, AvgTrades>2, 5-min
cap" — and let the user approve or redirect **before** generating.

## Step 2 — Generate (emit + self-verify, no install writes yet)

```python
from engine.generate import make_project
import os, glob

INSTALL = r"<install folder>"
BASE    = r"<install>\user\projects\<base folder>\project.cfx"   # from catalog
TPL_DIR = r"<install>\user\settings\StrategyTemplates\<set>"     # from catalog

picks = sorted(glob.glob(os.path.join(TPL_DIR, "*.sqx")))        # or a chosen subset
tasks = [{"template": p,
          "output_db": "BS-" + os.path.splitext(os.path.basename(p))[0],
          "avg_trades": 2, "time_minutes": 5} for p in picks]    # settings optional

report = make_project(BASE, "<NEW_PROJECT_NAME>", tasks,
                      out_cfx=os.path.join("engine", "out", "<NEW_PROJECT_NAME>", "project.cfx"))
print(report)
```
`make_project` clones the donor task per template, swaps the 4 holes, regenerates `config.xml`
(preserving the project tag + system databanks + inactive tasks), creates the databank folders next
to the emitted `project.cfx`, and **self-verifies**. A worked batch is in
`examples/gen_project_example.py` — copy it.

`output_db` must be **unique per task** (the engine asserts it). The proven convention is `BS-<stem>`
(the install's own fleet used a `_LS`/`_Long` suffix — any unique label works, just keep it consistent;
the engine keeps the task title, the internal Output value, and the `<Databank>` registration in sync).

## Step 3 — Validate (the engine does this; don't skip reading it)

`make_project` returns a report and raises on any failure. It checks: one `Build-Task{N}.xml` per task,
build-task count matches, output databanks **unique + registered** (an `output_db` colliding with a
system/preserved databank raises), the 5 **system databanks survived**, every other config section
(e.g. `<Resources>`) **preserved verbatim**, and each task's `templateFile` **resolves on disk** and
equals its intended template, with the internal Output value == the task title. The report's `notes`
key lists donor-state corrections and WARNINGs (enabled acceptance, `time-limit` stop type, untouched
foreign charts on 2-chart donors) — **surface them to the user**. Don't report success unless the
report comes back clean. (For an
independent faithfulness check — every clone == donor + exactly the 4 swaps — see `evals/run_evals.py`.)

## Step 4 — Deploy into the install + build-confirm (SQX CLOSED)

```python
from engine.generate import deploy
deploy(out_cfx=r"engine\out\<NAME>\project.cfx", install=INSTALL, project_name="<NAME>")
```
`deploy` copies the project into `<install>\user\projects\<NAME>\`, backs up any existing one, and
creates the databank folders. **Confirm SQX is closed first.** Then tell the user to open SQX, open the
project, and **run a Build** on one task. That build is the final proof.

> Status: the engine reproduces the **build-confirmed** task-wiring mechanic
> (`_attach_breakout_fleet.py`) **byte-faithfully** (every clone == donor + the 4 swaps), and
> emits structurally verified projects. A user build-confirm of an *engine-generated* project is the
> last step that earns it outright — do it once, then it generates fleets at scale.

## When to push back

- A base project whose build tasks are **not template tasks** (no `<StrategyType templateFile>`) →
  the clone has no template hole; pick a base whose tasks build from a template, or the user must set
  one up once.
- **Duplicate output databanks** → tasks collide on results; the engine refuses. Make each unique.
- Templates that **don't live inside the target install** → absolute paths won't resolve on another
  machine; move the `.sqx` into `user/settings/StrategyTemplates/…` first (or accept it's machine-local).
- "Change the symbol / timeframe / dates / trading options" → use `overrides` (see *Project-level
  OVERRIDES* above). The target symbol must exist in `sqcli -symbol action=list`; SQX heals its tick
  economics on load. If the symbol has **no data on the install**, SQX cannot resolve it — clone a base
  that trades it or have the user import the data first. Never fabricate tick size / point value.
- Deploying while **SQX is open** → it will clobber the edits on close. Stop; have the user close SQX.

## Reference

- `catalog.json` — what THIS install can clone + wire (read it first).
- `reference/project-grammar.md` — what a `project.cfx` IS (the ZIP model, the 4 holes, the system
  databanks, the SQX-closed rule, absolute-path resolution, the lab→product lineage).
- `examples/gen_project_example.py` — copyable base+templates → project.cfx batch.
- `engine/` — `discover.py` (install → catalog) · `generate.py` (`make_project` clone+wire+self-verify,
  `deploy` install placement).
- `evals/run_evals.py` — deterministic STRUCTURE self-test (faithful-clone + guardrails). Structure
  only; an AlgoWizard Build is the oracle.
