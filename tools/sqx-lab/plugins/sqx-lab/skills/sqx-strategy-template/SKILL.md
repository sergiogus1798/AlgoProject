---
name: sqx-strategy-template
description: Turn a trading idea into a StrategyQuant X strategy template for this project — ask the exact logic, check the block exists (authoring it with sqx-custom-block if not), emit the .sqx with the owner's defaults (his condition fixed plus one free random condition) or, when asked, one of the vendor's build-confirmed shapes, file it in the template library and install its blocks on both workers. Authoring only, no SQX run and no CPU burnt. Use when the owner describes an entry idea, a signal or a condition, or asks to create, build or design a template.
allowed-tools: Bash(python:*), Bash(py:*), Read, Write, Edit, Glob, Grep, AskUserQuestion
---

<!-- ALGOPROJECT OVERLAY START -->
## AlgoProject — read this first. Where it differs from the vendor text below, this wins.

Owner, 2026-09-25: this is the project's template skill; the old `/strategy-template` is retired.
Nothing here starts SQX or burns CPU. Building the template on a market is `/template-run`.

**1 · Ask the logic, always** (CLAUDE.md hard rule 11). "Closes above the band" fires on every
bar of a move, "crosses above it" fires once: different strategies. List the readings you see —
which band, state or transition, which price, which shift — and ask. The vendor's "clarify only
what you cannot infer" does not apply to the entry logic.

**2 · The owner's defaults win** (`sqx/templates/README.md`). Apply them silently, then say which
ones you applied:

| unspecified | assume |
|---|---|
| direction | long |
| extra conditions | ONE random condition, **free**: `#Group#` empty, the whole vocabulary |
| what he named | **fixed** exactly as said, never parametrised |
| periods, deviations he did not name | optimizable |
| `Shift` | 1 |

The vendor's thesis-driven shapes — filter + trigger bound to clean groups, stop/limit entries,
session gating, multi-timeframe, short or mirrored sides — are used **only when the idea or the
owner asks for one**. Do not launch the research agent for a default template.

**3 · Default path** — from the repo root, not the skill folder:

```bash
python3 -m sqx.inspect.vocabulary <term>         # does the exact block exist? native or his own
# missing -> author it with sqx-custom-block (its own overlay says how to install it)
python3 -m sqx.templates.build <name> <library>/<name>/deps/blocks.xml <CBlock_key> \
    <library>/<name>/template.sqx                 # market_long skeleton: fixed block AND free hole
# a NATIVE block: pass the conductor's AlgoWizard config.xml instead of deps/blocks.xml —
#   ~/Desktop/SQX_w1/internal/web/SQWIZARD/branding/global/config.xml
# fix what the owner named with --param, e.g. an EMA: --param '#Type#=1'
```

Never substitute the nearest existing block for the one the owner described. `vocabulary` printing
`NO GROUP POOLS IT — unusable in a template` concerns the random hole only: the fixed half of the
signal reaches any block directly, pooled or not.

**4 · Another shape** — the vendor flow below (catalog, design, `from_design`, validate), run from
the skill folder. Its output in `engine/out/` is scratch: copy it into the library (step 5).

**5 · Every template lands in the library**, `~/Desktop/AlgoData/templates/library/<name>/`:
`template.sqx`, `brief.md` (Spanish, the thesis and every default applied), `brief.json`,
`manifest.json`, `deps/` (`blocks.xml`, `groups.xml` when it has any). Copy the structure of
`keltnerUpperCrossUp`. The name never carries a symbol or a timeframe — those are rows in `runs.csv`.

```bash
python3 -m sqx.templates.registry --set name=<name> --set archetype=<breakout|meanReversion|…> \
    --set shape=<market_long|…> --set entry=… --set created=<date> --set origin=authored \
    --set status=validated
```

**6 · Its blocks and groups go into both workers**, stopped, never the master (CLAUDE.md hard
rule 3: check `ListAgents`, `ls -lt <worker>/user/projects | head` and the log first):

```bash
python3 -m sqx.blocks.install <deps/blocks.xml> --role conductor    # then --role custodian
python3 -m sqx.blocks.install <deps/groups.xml> --role conductor    # same tool for groups
python3 -m sqx.inspect.vocabulary --diff custodian                   # must report no gap
bin/sqx-lab-install.sh                                               # the catalogs are stale now
```

A template referencing a block the building install lacks does not error: it disappears from the
build. The vendor's "import into AlgoWizard and run a Build" does not apply here — the owner rarely
opens the GUI. `status=buildConfirmed` is written only by `/template-run`.

<!-- vendor text follows -->
<!-- ALGOPROJECT OVERLAY END -->
# sqx-strategy-template — author SQX/AlgoWizard strategy templates

Turn a trading idea — "breakouts only in the trend direction", "a session-filtered momentum
entry" — into an importable AlgoWizard **strategy template** (`.sqx`), built from **this** install's
own random groups and custom blocks. Third in the suite: `sqx-custom-block` builds the rules,
`sqx-random-group` pools them, **this skill wires the pools into a buildable strategy template.**

How it works: `discover.py` reads the install → a catalog of CLEAN random groups (Condition pools =
filters/triggers, Value pools = price levels); the **research agent** (`research_agent.md`) reasons
over that catalog and emits a **design spec**; `generate.py` transplants the chosen groups into a
**build-confirmed skeleton** and self-validates.

**Prerequisite:** Python 3.8+ (standard library only). A StrategyQuant X **build-144** install.

> **Run from the skill folder.** The `python engine/…` commands below use paths relative to
> **this skill's own directory** (where this `SKILL.md` lives) — run them from there, not from
> your project's working directory.

---

## The one idea (read once)

A SQX strategy is a **typed expression program**; a *template* is that program with some
sub-expressions replaced by typed **holes** (`RandomCondition`/`RandomValue` → a random group) plus
metadata for how to fill and vary them. This skill does NOT hand-write strategy XML — the type
system is necessary but **not sufficient** (engine exclusions, MagicNumber wiring, the signal-variable
protocol, mirror discipline all live outside the schema; only an actual *build* proves validity). So
it **transplants chosen groups into a proven skeleton and varies only the holes** — staying strictly
inside build-confirmed territory. Full model: `reference/strategy-grammar.md`.

## Shapes the generator can emit

Each shape = a proven skeleton + which holes it exposes. **Status is honest** — only build-confirmed
shapes are proven; the rest are validated (XML well-formed, groups resolve) but await a user build.

| Shape | Entry | Holes | Status |
|---|---|---|---|
| `stop` | pending stop, fills on a level | filter + trigger + **value** (stop price) | ✅ build-confirmed |
| `market` | immediate fill | filter + trigger | ⏳ validated, pending build-confirm |
| `market_single` | immediate fill | one condition | ⏳ validated, pending build-confirm |
| `session_market` | market + a non-directional time gate | filter + trigger (+ gate) | ✅ build-confirmed |
| `stop_long_single` | **long-only**, one condition, pending stop on a level | trigger + **value** (stop price) | ⏳ validated, pending build-confirm |
| `two_entry_market` | **long-only, two independent legs** — each its own condition, MagicNumber, ExitAfterBars | entry_a + entry_b | ✅ build-confirmed |
| `multi_leg` | **long-only, N independent legs** — each leg its own group + order type (market/stop) + ExitAfterBars + MagicNumber | `legs[]` (see below) | ⏳ validated, pending build-confirm (generalizes the confirmed `two_entry_market`) |
| `role_market` | **role-structured** market entry — `regime AND trigger AND NOT veto` (real boolean depth + a negated veto slot); short mirrors (`!regime AND !trigger AND veto`) | regime + trigger + **veto** (negated) | ⏳ validated, pending build-confirm (first shape with 3 condition holes + a NOT slot; built on the confirmed `stop` signal-var architecture, no bars-guard) |
| `mtf_filter` | **multi-timeframe** entry — a HIGHER-timeframe (daily) regime filter `AND` a main-TF trigger, entered on a stop at a level; short mirrors | **daily** filter (`#Chart#=1`) + trigger + **value** (stop price) | ⏳ validated, pending build-confirm (first shape on design axis **A** — a 2-stream `<Datas>` + a filter hole bound to the daily subchart; same signature as `stop`, MTF mechanic proven by the install's own `highest_breakout_template_daily_filter`) |
| `stop_long` | **long-only** twin of `stop` — short mirror stripped | filter + trigger + **value** (stop price) | ✅ build-confirmed (2026-06-10, the 24-template `breakout_fleet_long`) |
| `market_long` | **long-only** twin of `market` | filter + trigger | ✅ build-confirmed (2026-06-10) |
| `mtf_filter_long` | **long-only** twin of `mtf_filter` | **daily** filter (`#Chart#=1`) + trigger + **value** (stop price) | ✅ build-confirmed (2026-06-10) |
| `stop_short` | **short-only** — sell-stop at a breakdown level | filter + trigger + **value** (stop price, must be a **LOWER**-level pool) | ⏳ architecture matches a hand-corrected working set; engine-generated template pending build-confirm |
| `mtf_filter_short` | **short-only** MTF — daily regime + main-TF trigger, sell-stop | **daily** filter (`#Chart#=1`) + trigger + **value** (lower levels) | ⏳ same lineage as `stop_short` |
| `market_short` | **short-only** market entry | filter + trigger | ⏳ weakest: inherits `market`'s unconfirmed lineage, no working reference of its own |

> **Short shapes are NOT long shapes flipped — read this before designing one.**
> The two-sided skeletons carry a mirror signal (`generate="opposite"`) that resolves each
> pooled block through its `oppositeBlockKey`. That only works for **directional** blocks —
> a session/time filter is non-directional (`CBlock_null`), so any pool containing one
> silently breaks. The short shapes therefore **empty the mirror signal** and fire on the
> *primary* signal with `#Direction#=-1`.
>
> **Consequence:** a short design must name genuinely **bearish** groups — a "prior-low
> breakdown" trigger, a "trend-down" filter, a **lower**-level Value pool. Nothing mirrors
> them for you. Pointing `stop_short` at an upper-level price pool gives you a sell-stop
> *above* the market, which can never fill correctly.

A *filter* = regime/context (WHEN we may act); a *trigger* = the entry event (WHAT fires). Short side
always mirrors automatically (`NegatedCondition` / `OppositeValue`). The full exit stack
(SL/PT/Trailing/MoveSL2BE/ExitAfterBars) is already present in every skeleton — the template only
decides which exits are optimizable vs frozen (see `reference/strategy-grammar.md`).

---

## Step 0 — One-time setup: ASK FOR THE SQX INSTALL FOLDER (mandatory)

> **`/sqx-setup` does this step for all four skills at once**; `/sqx-doctor` reports health,
> including whether this skill has the groups it needs.

**Shared install path — check first.** All four sqx-lab skills share one stored SQX folder:
`~/.sqx-lab/sqx-install.txt` (override the directory with `SQX_LAB_HOME`) — outside the plugin
folder, so a plugin update doesn't wipe it. Written automatically after the first successful
bootstrap of *any* sqx-lab skill. If it exists, `python engine/discover.py` with **no argument**
uses it — tell the user which folder is being used and only re-ask if they say it's wrong (then
re-run with the corrected folder, which updates the stored path). A path is stored only after it
validates as a real SQX install.

Otherwise: there are often several SQX installs on one machine. **You MUST ask the user which
install** — the top-level folder (with `internal/` and `user/`), e.g. `C:\StrategyQuantX`.
Do not auto-pick. Then:

```
python engine/discover.py "<the folder the user gave>"
```

This writes `catalog.json` next to the engine and prints a summary:
- **CLEAN Condition groups** — usable as filters/triggers (a group is clean iff every `CBlock_*` it
  references exists in the install's `customBlocks.xml`; broken groups are excluded automatically).
- **CLEAN Value groups** — usable as stop/limit price pools.

`catalog.json` is your source of truth for what THIS install can wire. Consult it; never invent a
group name. (`sqx-random-group` is how you *create* a new group if the catalog lacks one you need.)

### If discover reports BROKEN groups — offer the repair, don't just move on

A group is BROKEN when it references `CBlock_*` blocks that aren't in this install's
`customBlocks.xml` — typically the group was imported (or survived a reinstall) but its blocks
weren't. Broken groups are excluded from every design, so this silently shrinks what you can
build, and **a broken Value group is the worst case: with no clean Value group, `stop`,
`stop_long` and `mtf_filter` — every build-confirmed shape — become ungenerable.** `discover.py`
warns about exactly this.

Do not just design around it. `catalog.json` carries a **`repair_manifest`**: per broken group,
each missing block's `key`, `block_type` (`Condition` / `Price level`), and `rule` — AlgoWizard's
own display text, e.g. `Close > HighD[1]` or `(Close - VWAP) > #Double4# * ATR`. That is enough
to re-author them. The loop:

1. Tell the user what's broken and what repairing it would unlock (name the shapes).
2. Hand the manifest to **`sqx-custom-block`** — the rule text drops straight into its Step 2.
3. User imports the emitted XML into AlgoWizard (Custom Blocks → import).
4. Re-run `python engine/discover.py` → the group flips to CLEAN and its shapes unlock.

**Repair a broken Value group first** — one repair restores every build-confirmed shape.

Honest caveat: `Price level` entries often carry only a name (`CBlock_PrevDayHigh`,
`CBlock_KamaUpperBand`) instead of an expression, because AlgoWizard stores no display text for
them. Re-derive those from the name and **confirm with the user before authoring** — don't guess
a level's definition silently.

## Step 1 — Clarify or let the agent propose

If the user gave a concrete idea, capture it. If they want options, the **research agent designs
them** — read `research_agent.md` and reason over `catalog.json` to produce design specs. If they want
you to **source edges from the literature** ("propose options", "what's worth building"), first run the
optional autonomous front-end in `research_sourcing.md` (WebSearch/WebFetch → falsification gate →
install-bound candidates), then feed its survivors into the design agent. Either way, every group named
in a design must exist in `catalog.json` with the right type.

## Step 2 — Design spec (the research agent's job)

Following `research_agent.md`, pick a named **archetype**, instantiate its roles from this install's
real groups (one filter + one trigger — never two of a kind), pair for confluence not redundancy, pick
the shape/execution, and write a **falsifiable thesis** (if you can't say *why* the edge should exist,
drop it). Use the **real catalog names** (`Entries*` triggers, `Filter*` filters, `Levels*` value
pools) — the legacy `TrendUP`/`BreakoutUP`/`BreakoutChannels` do not exist in this install. Spec schema:

```json
{ "name": "TrendFilteredBreakout", "shape": "stop",
  "filter": "FilterTrendDirection", "trigger": "EntriesBreakout", "price_pool": "LevelsPriorPeriod",
  "roles": { "FilterTrendDirection": "regime filter", "EntriesBreakout": "breakout trigger",
             "LevelsPriorPeriod": "stop level" },
  "thesis": "Breakouts taken only in the trend regime follow through more than counter-trend ones." }
```
(`market`/`session_market`: `filter` + `trigger`, no `price_pool`. `market_single`: `condition`.)

**`mtf_filter`** — multi-timeframe: a daily regime filter `AND` a main-TF trigger → stop at a level.
The `daily_filter` group is evaluated on the daily subchart (`#Chart#=1`); the short side mirrors and
inherits the daily binding automatically:
```json
{ "name": "MTFTrendBreakout", "shape": "mtf_filter",
  "daily_filter": "FilterTrendDirection", "trigger": "EntriesBreakout", "price_pool": "LevelsPriorPeriod",
  "roles": {"FilterTrendDirection": "daily regime (HTF)", "EntriesBreakout": "intraday trigger",
            "LevelsPriorPeriod": "stop level"},
  "thesis": "Intraday breakouts aligned with the DAILY trend follow through more than ones that fight it." }
```

**`role_market`** — role-structured entry with real boolean depth and a veto slot
(`regime AND trigger AND NOT veto`; short mirrors automatically). Three distinct Condition
groups, no `price_pool`:
```json
{ "name": "TrendBreakoutVetoExhaustion", "shape": "role_market",
  "regime": "FilterTrendDirection", "trigger": "EntriesBreakout", "veto": "EntriesMeanRevert",
  "roles": {"FilterTrendDirection": "regime", "EntriesBreakout": "trigger", "EntriesMeanRevert": "veto"},
  "thesis": "Trend-aligned breakouts, but VETO any coinciding with a reversal signal (exhaustion breaks)." }
```
The veto is the edge: it must name a condition you want to *exclude* at entry (a context that
spoils the setup), not a second confluence filter. `regime`/`trigger`/`veto` must be three
*distinct* Condition groups.

**`multi_leg`** — N independent entry legs (each a separate setup with its own group, order type,
exit timing, and MagicNumber; all long-only; exit per-leg via ExitAfterBars only):
```json
{ "name": "MyMultiLeg", "shape": "multi_leg", "legs": [
    { "group": "EntriesBreakout", "order": "market", "exit_bars": 10 },
    { "group": "EntriesTrend",    "order": "stop", "price_pool": "LevelsPriorPeriod", "exit_bars": 30 }
] }
```
`order: "stop"` legs require a `price_pool` (a Value group); `order: "market"` legs don't. Each leg
should carry its own thesis — two legs that fire on near-identical conditions are one strategy
booked twice, not two edges.

State each spec in plain English and let the user approve or redirect **before** generating — the
cheapest place to catch a wrong design.

## Step 3 — Generate

```python
from engine.generate import from_design
from_design(spec, install=r"<install folder>")   # → writes engine/out/<name>.sqx
```
The generator looks the groups up, checks each type (Condition for filter/trigger, Value for price
pool), points the `RandomCondition`/`RandomValue` holes at them, embeds the groups, renames, and
**self-validates** (blocks resolve, group refs embedded). A worked batch is in
`examples/gen_template_example.py` — copy it.

## Step 4 — Validate (the generator does this; don't skip reading it)

`from_design` raises `VALIDATION FAILED` if any `CBlock_*` doesn't resolve or a `#Group#` ref isn't
embedded. Don't report success unless it prints `OK`.

## Step 5 — Hand off + build-confirm

Tell the user to import `engine/out/<name>.sqx` into AlgoWizard and **run a Build**. For a shape that
is still ⏳ pending, the build is what earns it. Report results faithfully; on a build error, fix the
specific shape/skeleton — don't rewrite everything.

## Adding a NEW shape (the lab→product loop)

New structure (limit fill, grid/pyramid, OR-trees, a different gate) = a new region of the design space.
**Never hand-write novel strategy XML from the grammar alone** — derive the new skeleton from a
template in the install that ALREADY exhibits the structure. Two worked examples: `proto_session_gate.py`
derived `session_market` from the install's `highest_breakout_template_daily_filter` by wrapping each
entry signal in `AND(condition, BarDayOfWeekIsNot)`; `build_mtf_filter_skeleton.py` derived `mtf_filter`
(design axis A — multi-timeframe) from the build-confirmed `stop` skeleton by transplanting just the MTF
mechanic proven in that same daily-filter template (a 2-stream `<Datas>` + one filter hole on `#Chart#=1`).
Then: user imports + **build-confirms once** → register the shape in `engine/generate.py` `SHAPES` → it
generates at scale thereafter. Same loop the
block and group skills use. Known-available, not-yet-skeletoned regions are listed at the bottom of
`reference/strategy-grammar.md`.

## When to push back

- A group name not in `catalog.json` → it isn't in this install; build it with `sqx-random-group`, or
  pick one that is.
- Two filters or two triggers in one design → redundant; pair a filter with a trigger.
- A `stop`/limit price pool on the wrong side of the trade → fix the pool (upper levels for longs-up).
- A request for a shape not in the table → it needs the lab→product loop above first; say so.
- "Just hand-write the XML for X" → only if a build-confirm follows; otherwise it's unproven.

## Reference

- `catalog.json` — what THIS install can wire (read it first).
- `research_agent.md` — the design-reasoning layer (the **archetype taxonomy**, the 3-axis regime model,
  confluence/redundancy, roles, falsifiable thesis, edge hygiene).
- `research_sourcing.md` — the optional autonomous front-end (source edges from the literature →
  falsification gate → install-bound candidates that feed the design agent).
- `reference/strategy-grammar.md` — what a SQX strategy/template IS (the abstract model + design space + the validity gap).
- `examples/gen_template_example.py` — copyable design→.sqx batch.
- `engine/` — `discover.py` (install → catalog) · `generate.py` (design spec → .sqx, self-validating) ·
  `proto_session_gate.py` / `build_mtf_filter_skeleton.py` (how a new shape is derived from a proven
  install template) · `skeletons/` (the proven build skeletons).
- `evals/run_evals.py` — deterministic STRUCTURE self-test. Runs against a **committed fixture install**
  (`evals/fixtures/`) by default, so it works on a fresh machine with no groups authored yet;
  `--install "<SQX folder>"` additionally exercises your real groups. Exit `0` pass / `1` regression /
  `2` SKIPPED-nothing-ran. Structure only; an AlgoWizard Build is the correctness oracle.
  Includes the `*_short` architecture invariants — mirror signal empty, `#Direction#=-1`, entry fires
  on the primary signal — so the short shapes can't silently regress to the broken mirror variant.
