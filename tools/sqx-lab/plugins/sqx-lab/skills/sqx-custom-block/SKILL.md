---
name: sqx-custom-block
description: Author StrategyQuant X / AlgoWizard custom blocks (trading rules) as importable XML, from a plain-English idea. Discovers the indicator vocabulary from the user's OWN install (config.xml + optional customBlocksExport.xml) and builds both Condition blocks (true/false rules) and Price-level blocks (that return a price — stops, targets, bands, breakout references), validating them before import. Use when the user asks to create, build, or author an SQX/AlgoWizard custom block, signal, filter, entry/exit rule, or a price level / band / stop / target level.
allowed-tools: Bash(python:*), Bash(py:*), Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# sqx-custom-block — author SQX/AlgoWizard custom blocks

Turn a trading idea into an importable AlgoWizard custom block. The skill is portable:
it does **not** assume a particular SQX build or indicator set — it discovers what *this*
user can build from their own install, then assembles and validates the XML.

AlgoWizard has **two block types**, both authored here: **Condition** blocks (the default —
a true/false rule, Steps 1–7 below) and **Price-level** blocks (return a *price* — a stop /
target / band / breakout reference). If the request is for a *level / band / stop / target*
rather than a yes/no signal, jump to **"The other block type — Price levels"** near the end;
it reuses the same Steps 1–5b with one different wrapper.

How it works: an indicator entry in the user's `config.xml` is already ~90% of a usable
block atom. `bootstrap.py` reads their `config.xml` (+ optional `customBlocksExport.xml`)
into a catalog; `emit.py` rebuilds any atom block-ready; `grammar.py` supplies the
build-stable operators and the `CBlock_*` wrapper; `validate.py` gates the result.

**Prerequisite:** Python 3.8+ (standard library only — no pip installs).

> **Run from the skill folder.** The `python engine/…` commands below use paths relative to
> **this skill's own directory** (where this `SKILL.md` lives) — run them from there, not from
> your project's working directory.

---

## Step 0 — One-time setup: ASK FOR THE SQX INSTALL FOLDER (mandatory)

Do this **once per machine**, before the first block request. If `catalog.json` already
exists next to this skill, skip to Step 1.

> **`/sqx-setup` does this whole step for all four skills at once**, and `/sqx-doctor`
> reports what is and isn't set up. If nothing has been bootstrapped yet, point the user
> at `/sqx-setup` instead of walking them through this four times.

**Shared install path — check first.** All four sqx-lab skills share one stored SQX folder:
`~/.sqx-lab/sqx-install.txt` (override the directory with `SQX_LAB_HOME`), written
automatically after the first successful bootstrap of *any* sqx-lab skill. It sits outside
the plugin folder deliberately, so a plugin update no longer wipes it. If it exists, running
`python engine/bootstrap.py` with **no arguments** uses it — tell the user which folder is being
used ("using your stored SQX install at <path>") and only re-ask if they say it's wrong
(then re-run with `--install "<corrected folder>"`, which also updates the stored path).
Only when no stored path exists does the ask-first flow below apply.

A path is stored only **after** it validates as a real SQX install, so a wrong folder can
never silently break the other three skills. An invalid folder prints the exact file it
expected plus the fix — read that error to the user rather than guessing.

**On first use (no stored path) you MUST ask the user where StrategyQuant X is installed.**
Do not skip this. Do not silently auto-detect and proceed — asking for the folder is a required
step, even if a guess is available. The flow is:

1. **ASK the user for their StrategyQuant X install folder** — the top-level one, e.g.
   `C:\StrategyQuantX144` or `D:\SQX_...`. Pose this question (AskUserQuestion or plain prompt)
   and wait for the answer *before* building any catalog.
2. *(Optional, only to make answering easier)* run `python engine/discover.py` to **suggest**
   any installs found on this machine, then show the candidate(s) to the user and have them
   **confirm or correct** the folder. A discovered path is a suggestion to confirm — never a
   silent default, never adopted without the user saying "yes, that one".
3. Build the catalog from the folder the user gave/confirmed:
   `python engine/bootstrap.py --install "<folder>"`.
4. **None found / user unsure** → still ask; have them locate the top-level StrategyQuant X
   folder (the one containing `internal/` and `user/`), then `--install "<folder>"`.

> `--auto` exists for manual CLI convenience only — it auto-picks without asking, which defeats
> the required folder question. **Do not use `--auto` as the skill's setup path.**

You never dig for individual XML files — from the install root the skill auto-resolves **four
sources**, so **every** custom indicator the user has is covered, whatever state it is in:
- `…/branding/global/config.xml` → **native** built-in indicators **plus the user's OWN custom
  indicators that they've registered** in AlgoWizard. SQX stamps every registered custom with
  `customSnippet="true"`, so bootstrap separates them from the native built-ins and surfaces them
  as **YOUR custom indicators** (`✦`). **This is the primary, machine-independent way the skill
  recognises the user's indicators — it works whether or not the `.java` source is on disk, and
  is what fixes "it didn't find my indicator" on a machine that only has the registered config.**
- `…/user/settings/customBlocks.xml` → their custom indicators in **proven** form (any they've
  used in a block) — adds any not already in config.
- `…/user/extend/Snippets/SQ/Blocks/Indicators/<Name>/<Name>.java` → their **coded** custom
  indicators, read straight from the Java source (`@BuildingBlock`/`@Parameter`/`@Output` give
  the exact display, knobs, outputs). Supplementary: catches an indicator coded but NOT yet
  registered into `config.xml`, and gives the highest-fidelity schema. (Companion `ConditionBlock`
  files — `...AboveLevel`, `...CrossUP` — are boolean signals, not value atoms, and are skipped.)
- `…/branding/global/UserCustomIndicators.xml` → a small registry of custom indicators
  (**synthesized**, flagged `✎`, verify on first import)

`bootstrap` and `catalog.md` both open with a **⭐ YOUR custom indicators** section that lists
every one of the user's own indicators **by name** with its contract — so the user immediately
sees their indicators were found, never silently absorbed into the native list.

(Manual override is always available: `python engine/bootstrap.py <config.xml> [--export ...]
[--snippets ...] [--user-indicators ...]`.)

Writes `catalog.json` (machine) and `catalog.md` (human report). **Read `catalog.md`** — it opens
with the **⭐ YOUR custom indicators** section, then lists every usable atom with display, return
type, oscillator midline, the period/double knobs you can optimize, and flags (`⚠`=talib/unusable,
`◆`=multi-output, `✦`=YOUR custom indicator — from the config `customSnippet` marker, an export, or
a Java snippet, `✎`=synthesized). This is your source of truth for what exists — consult it, do not guess.

> **Multi-source rule (load-bearing):** an indicator the user has is usable even if it is NOT a
> native built-in. Most of the user's customs are registered in `config.xml` (marked
> `customSnippet="true"` — surfaced as **YOUR custom indicators**); the rest come from their
> exports / `.java` snippets / registry. Never tell a user an indicator is unavailable until
> you've checked the catalog built from all four sources.

### Using the user's own custom indicators
- **Registered in AlgoWizard (the common case)** → it's already in `config.xml` with
  `customSnippet="true"`; bootstrap surfaces it as one of **YOUR custom indicators** (`✦`) and it
  works exactly like a native atom — no `.java` needed: `cat.atom("CSSAMarketRegime")`,
  `cat.atom("MACDV", line="0")`.
- **Already used in a block** → it's in `customBlocksExport.xml`; bootstrap harvests it
  **proven**. Use it like any native atom: `cat.atom("CMMA", lookback="#Int2#")`.
- **Coded in the editor (compiled snippet)** → bootstrap reads its `.java` source under
  `user/extend/Snippets/.../Indicators/` and reconstructs the atom from the annotations (`✦`).
  This is how the skill finds an indicator the user wrote but has **not** registered into
  `config.xml` — the single most common "why didn't it find my indicator?" cause. Use it like
  any atom; flag "verify on first import".
- **Built but never used in a block** → it's in `UserCustomIndicators.xml`; bootstrap
  **synthesizes** it (`✎`). It will import, but the synthesized display/params are best-effort
  — flag "verify on first import" in your hand-off.
- **Guaranteed-correct path for a `✎` atom:** tell the user to drop it into one throwaway
  custom block in AlgoWizard, export, and re-run bootstrap — it then arrives **proven** and
  the `✎` flag disappears. Offer this whenever you emit a synthesized atom.

---

## Research mode — when the user wants ideas, not a specific rule (optional front-half)

If the user asks *"what blocks should I build for X?"* / *"find me momentum strategies"* / hands
you a paper or a theme rather than a concrete rule, run the research front-half first, then feed
its output into authoring. (The skill is the *how*; this step is the *what*.)

The flow is **propose → critique → gate → author → assess**. A proposer alone inflates; the critic
forces each edge to earn its place (SQX mass-tests blocks, so a weak one manufactures an overfit
strategy that loses live).

1. **PROPOSE — spawn a research subagent per theme** (Agent tool, type `web-search-agent` or
   `general-purpose`). Task = `reference/research-prompt.md`, fill `{THEME}` and `{CATALOG_PATH}`.
   It returns specs each carrying a **falsifiable hypothesis**, edge family, regime, failure mode,
   and an honest `repaint_risk`. Spawn several in parallel for breadth (one theme each). Save the
   JSON to `specs.json`.
2. **CRITIQUE — spawn an adversarial critic** (Agent tool, type `general-purpose`). Task =
   `reference/critic-prompt.md`, fill `{SPECS_JSON}`, `{CATALOG_PATH}`, and `{EXISTING_LIBRARY}`
   (names of blocks the user already has, so duplicates get caught). It scores each spec on
   rationale / overfit / novelty / repaint / buildability and returns KEEP / REVISE / KILL.
   **Drop the KILLs; apply the REVISE fixes** (use the critic's `revised_spec` when given) → a
   pruned `specs.json`.
3. **GATE — mechanical catalog check:** `python engine/check_specs.py specs.json --catalog catalog.json`.
   Rejects phantom atoms and talib, flags multi-output, and surfaces cheap quality hints
   (repaint-likely, >2 knobs, missing hypothesis). Only `BUILDABLE`/`BUILDABLE*` proceed — never
   author a `BLOCKED` spec.
4. **PRESENT** the survivors to the user as a short table (name · rule · edge family · confidence ·
   source), established before speculative. Let them pick which to author.
5. **AUTHOR** the chosen ones via Steps 2–5 below — each spec carries name, rule, atoms, operator,
   params, and category, so it drops straight into Step 2.
6. **ASSESS — edge-hygiene the generated XML** (Step 5b below) before hand-off.

Keep it disciplined: catalog-grounded, sourced, hypothesis-backed, honest about
established-vs-speculative. The proposer must never name an atom outside the catalog, the critic
kills weak/duplicate/repainting edges, and `check_specs.py` enforces buildability.

## Repair mode — rebuilding blocks a random group is missing

If the user says *"repair my broken groups"*, or `sqx-strategy-template`'s discover reported
BROKEN groups, the work order is already written. Read `repair_manifest` from
`../sqx-strategy-template/engine/catalog.json`:

```json
{ "group": "Brk_PrevLevels_Long", "group_type": "Condition", "category": "Breakout",
  "rebuild": [ { "key": "CBlock_PrevDayHighBreak", "rule": "Close > HighD[1]",
                 "block_type": "Condition" } ] }
```

- **`key` is load-bearing** — emit each block with exactly that `key=` (`make_block(key=…)`),
  or the group still won't resolve. This is the one case where you do NOT get to pick the name.
- **`rule`** is AlgoWizard's own display text. Translate it into catalog atoms + an operator
  (`Close > HighD[1]` → `is_greater(cat.atom("Close"), cat.atom("HighD", shift="1"))`). Confirm
  every atom against `catalog.json` as usual — a phantom atom fails the same way here.
- **`block_type: "Price level"`** → use `make_price_level(...)`, not `make_block(...)`.
- **Price-level entries often carry only a name**, not an expression (`CBlock_KamaUpperBand`),
  because AlgoWizard stores no display text for them. **Propose your reading of the name and get
  the user to confirm before authoring** — silently inventing a level definition is worse than asking.
- Emit the whole group's missing blocks as **one batch XML**, validate + assess as normal, then
  tell the user to import it and re-run the template skill's discover to see the group go CLEAN.

Prioritise a broken **Value** group: repairing one restores every build-confirmed strategy shape.

## Step 1 — Clarify (only what you cannot infer)

- **The rule** in plain English (or a paper/blog/URL — extract the rule yourself).
- **Long-only or both?** Default: both, auto-paired via `oppositeBlockKey`.
- **Param ranges?** Default: sensible ranges (period 2–50, etc.).

## Step 2 — Spec in plain English BEFORE writing XML

For each block, state in chat: name, 1-line description, operator shape
(cross / level / rising / percentile / count / arithmetic), the indicator(s) — each
**confirmed present in `catalog.json`** — and the params with defaults + ranges. Let the
user approve or redirect before any XML.

**Default to clean single-signal blocks.** One block = one idea. Do **not** stack a second
confirming indicator with AND unless the user asks. A pattern that needs two bounds on the
*same* geometry (e.g. a session window's open+close hour) is still one signal — that is fine.

## Step 3 — Atom check (against the catalog, not memory)

For every indicator you plan to use:
```python
from engine.emit import Catalog
cat = Catalog("catalog.json")
cat.has("RSI")           # True/False — is it in this install?
cat.search("keltner")    # fuzzy find the real key
cat.info("MACD")         # returnType, midline, bindable knobs, multi_output
```
- Not in the catalog → it does not exist in this user's build. Pick an equivalent that is,
  and say so. Do **not** invent an atom (the "phantom atom" failure).
- Multi-output (`◆`, e.g. MACD/Stochastic/Aroon/Ichimoku) → choose the output with `line=`.
  `emit` carries the `#Line#` param automatically; you just pick which line.
- Read the **midline** from `catalog.md` before comparing an oscillator to a level. It is
  per-indicator and a frequent error source: RSI 50, CCI 0, Momentum **100**, Williams %R
  **−50**, Stochastic 50, DeMarker 0.5. Don't copy a midline from another indicator.

## Step 4 — Generate via a script

Copy `examples/gen_example.py`, change the block list, write to `<name>.xml`. Core API:
```python
from engine.emit import Catalog
from engine.grammar import (crosses_above, crosses_below, is_greater, is_lower,
    is_rising, and_op, make_block, int_param, double_param, esc, wrap_batch)

cat = Catalog("catalog.json")
contents = crosses_above(cat.atom("RSI", period="#Int2#"), cat.number("30", bind="#Double3#"))
block = make_block(
    key="CBlock_ReclaimOversold", name="ReclaimOversold",
    display=esc("RSI(@Chart@14) crosses above 30"), category="MeanReversion_user",
    help_text=esc("Long: RSI reclaims the oversold level."),
    opposite="CBlock_FailOverbought",
    params=int_param("#Int2#","RSI Period","14","2","50") + double_param("#Double3#","Oversold","30","5","45","1"),
    contents=contents)
```
Conventions (the emitter/grammar enforce most of these for you):
- Outer optimizer knobs: `#Int2#`, `#Int3#`, `#Double3#`, `#Double4#` … (one per tunable).
  Bind an atom knob to one by passing the friendly param name: `cat.atom("RSI", period="#Int2#")`.
  Every `#IntN#`/`#DoubleN#` you reference MUST be declared via `int_param`/`double_param`
  in that block's `params` (validator check 4 enforces this).
- Long/short pairs cross-link via `oppositeBlockKey`; use `"CBlock_null"` for a symmetric
  single block (e.g. a session-time filter that isn't directional).
- **Wrap every `display=` and `help=` string in `esc()`** — raw `<`, `>`, `&` break the parser.
  `emit` already escapes everything it generates.
- **Single timeframe by default.** Only pass `cat.atom(..., chart_tf="D1")` if the user
  explicitly asks for multi-timeframe.
- **OHLC reads the last CLOSED bar (shift ≥ 1).** `emit` defaults shift to 1 and **refuses
  `shift="0"`** on any OHLC/indicator atom — the developing bar is look-ahead on SQX/MT engines
  (only TradeStation reads it intrabar). Pass `allow_shift0=True` only if you truly target
  TradeStation. For a breakout, put the signal-bar OHLC at shift 1 and the **channel one bar
  further back (shift 2)** so it excludes the signal bar (`Close[1] > Highest[1]` can never fire).
- **Block `name=` must NOT end in `_<digits><letters>`** (e.g. `_144Native`, `_2v3`) —
  AlgoWizard strips that suffix and mis-renders opposite-block links. Safe: `_Long`,
  `_Filter`, `_user`. Validator check 6 enforces this.
- **Never use a `talib_*` atom** in a single-symbol/FX project — it throws a Stockpicker
  NullPointerException at build time. `emit` refuses them unless `allow_talib=True`
  (portfolio/stockpicker projects only).

## Step 5 — Validate (must pass before you declare done)

```
python engine/validate.py <name>.xml --catalog catalog.json
```
All checks must pass (warnings are allowed). Don't report success until they do. Check 7
(with `--catalog`) confirms every multi-output atom carries its `#Line#` and no talib atom
slipped in.

## Step 5b — Assess edge-hygiene (quality, not just correctness)

```
python engine/assess.py <name>.xml --catalog catalog.json
```
`validate.py` proves the block *imports*; `assess.py` proves it won't *quietly lose money*. It
grades each block (A–D) and flags the silent edge-destroyers a syntactic check can't see:
- **CRITICAL** = will distort the backtest or live results — **fix before import**: a value atom on
  the developing bar (`#Shift#=0`, look-ahead), a **repainting** indicator (fractals/ZigZag/
  HalfTrend/Gann/SuperTrend-type) read unconfirmed, or a threshold outside the indicator's range
  (the block can never fire).
- **WARN** = overfit/robustness risk: a repaint-family indicator (safe only at `shift≥1`),
  AND/OR compounding, or >3 tunable knobs.
- **INFO** = nits (a midline-level filter, an over-precise threshold).

Treat any **CRITICAL** as a must-fix. Re-emit the block (e.g. read the repainting atom at
`shift≥1`, fix the threshold) and re-assess. `--strict` makes it exit non-zero on any CRITICAL so
you can gate on it.

## Step 6 — Summarize + hand off

Give the user a short table (block name → plain-English rule → params) and tell them to
import `<name>.xml` into AlgoWizard (Custom Blocks → import). Note anything to verify on
first import (a brand-new user-custom atom, an assumed midline, an intraday-only atom).

## Step 7 — User imports, reports failures

Fix the specific failing block; don't rewrite the whole batch. If an atom fails to bind,
re-check its schema in `catalog.json` (a param key or `#Line#` mismatch is the usual cause).

---

## The other block type — Price levels (return a price, not true/false)

A **Price-level** block outputs a *price value* — a dynamic line used as a stop / target /
entry / breakout reference. It is a distinct **type**, not a category: `type="Price level"`,
`returnType="price"`, and its `<Contents>` is a single **VALUE expression** with **no
`and_op`/comparison wrapper**. (Do not confuse with a Condition block that *references* a
level, e.g. "Close crosses prior-day High" — that's still `type="Condition"`.)

Same workflow as above (Steps 1–5b: clarify → spec → atom-check against the catalog →
generate → validate → assess), with two differences:

1. **Use `make_price_level(...)`** instead of `make_block(...)` (identical signature; it just
   emits `type="Price level"` / `returnType="price"`).
2. **`contents` is a value, not a boolean** — one of:
   - a single **price atom**: `cat.atom("HighD", shift="1")` (any catalog atom whose
     `returnType` is `price` — OHLC, period OHLC, session levels, MAs, SuperTrend, Donchian,
     Keltner/Bollinger band lines, VWAP, …).
   - an **arithmetic tree** for `anchor ± k·volatility`:
     `plus(cat.atom("HullMovingAverage", period="#Int2#"), mult(cat.number("2", bind="#Double4#"), cat.atom("ATR", period="#Int3#")))`.
   - `maximum(...)` / `minimum(...)` for a confluence of several levels.

**Decide the block in this order:** *level-or-condition?* → **anchor** (which price series the
level sits on) → **buffer?** (`± k·ATR/StdDev`, with `k` a `cat.number(bind=…)` knob; double for
fractional multipliers) → **compose-or-wrap** (if a catalog indicator already emits that exact
level — e.g. a coded `*ATRBands` Upper line — wrap it instead of rebuilding from arithmetic) →
**mirror-or-solo** (upper↔lower bands cross-link via `oppositeBlockKey`; a single anchor or a
flip-trail is solo `"CBlock_null"`) → **shift** → **knobs**.

**Shift rule (load-bearing):** leaves read shift ≥ 1. The one exception is a **current-period
OPEN** (today/this-week/this-month open) — fixed the instant the period opens, so `shift="0",
allow_shift0=True` is correct there, *not* look-ahead. Never shift 0 for current High/Low/Close
(still forming). `assess.py` still flags repainting trails (SuperTrend/HalfTrend/SSL) read
unconfirmed — keep them at shift ≥ 1.

Worked template: **`examples/gen_pricelevel_example.py`** (a band pair + OHLC anchors + a
SuperTrend trail). `validate.py` and `assess.py` apply unchanged.

## When to push back

- 50+ blocks in one batch → split into themed batches of 15–25.
- Indicator not in `catalog.json` → it isn't in their build; propose an equivalent that is.
- A "duplicate" that differs only in default values → point at the existing block first.
- A request to stack confirmations into one block → check it's wanted; default is one signal.

## Reference

- `catalog.md` — what atoms this install actually has (read it first).
- `reference/lessons.md` — the hard-won rules, with the *why* behind each guard.
- `reference/grammar.md` — the block XML format, so you can read/debug emitted output.
- `reference/research-prompt.md` — the PROPOSER agent task (hypothesis-grounded candidate specs).
- `reference/critic-prompt.md` — the adversarial CRITIC agent task (kills weak/overfit/repaint specs).
- `examples/gen_example.py` — the copyable batch template (Condition blocks).
- `examples/gen_pricelevel_example.py` — the copyable template for **Price-level** blocks (band / OHLC anchor / trail, via `make_price_level`).
- `engine/` — `bootstrap.py` (discover) · `emit.py` (build atoms) · `grammar.py` (operators +
  wrapper) · `check_specs.py` (gate specs) · `validate.py` (correctness lint) · `assess.py`
  (edge-hygiene lint).
- `evals/run_evals.py` — deterministic self-test (8 cases: regenerate the examples and assert the
  guardrails fire) you can run against your own bootstrapped catalog: `python evals/run_evals.py`.
