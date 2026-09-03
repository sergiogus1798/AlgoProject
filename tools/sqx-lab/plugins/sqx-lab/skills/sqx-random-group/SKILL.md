---
name: sqx-random-group
description: Author StrategyQuant X / AlgoWizard random groups (the pools the strategy builder samples from) as importable XML. Discovers what THIS install can pool from its own config.xml + customBlocks.xml, and builds both Condition groups (boolean rule pools) and Value groups (price/level pools), in two item modes — hybrid (re-export existing custom blocks by reference) and inline (fresh rules / value atoms / comparisons) — validating before import. Use when the user asks to create, build, or author an SQX/AlgoWizard random group, block group, building-block pool, or a "Same condition / Same value" pool for a strategy template.
allowed-tools: Bash(python:*), Bash(py:*), Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# sqx-random-group — author SQX/AlgoWizard random groups

Turn "a pool of breakout triggers" or "group my trend blocks" into an importable AlgoWizard
random-group XML. Portable: it discovers what *this* user can pool from their own install, then
assembles and validates the XML. Sibling to `sqx-custom-block` — a group *pools* blocks/atoms;
a block *is* a rule. (Build the blocks with that skill; pool them with this one.)

How it works: `bootstrap.py` reads the install's `config.xml` (inline rule + value-atom
templates) and `customBlocks.xml` (the user's `CBlock_*` blocks) into a catalog; `groups.py`
emits the two item modes + the `<Group>` wrapper; `validate.py` gates the result.

**Prerequisite:** Python 3.8+ (standard library only).

> **Run from the skill folder.** The `python engine/…` commands below use paths relative to
> **this skill's own directory** (where this `SKILL.md` lives) — run them from there, not from
> your project's working directory.

---

## How random groups work (read once)

A random group is a **menu the builder draws ONE item from per strategy**, to fill a single slot.
Its contents override the global Building-Blocks settings for that slot. A strategy template binds
a group to a placeholder — **`SameCondition`** (a `type="Condition"` group), **`SameValue`**
(`type="Value"`), or `SameAction` — by the group's **UUID**. So a group is a *curated alternative
set per slot*, not a rule itself.

Two ways to fill a group (you can mix neither — pick per group, but both can appear in a set):
- **HYBRID** — pool the user's existing custom blocks by reference (`CBlock_*`). The common case.
- **INLINE** — build fresh items from catalog atoms: a `simpleRules` boolean, a bare value atom,
  or one operator comparison.

See `reference/groups.md` for the format. Items are **flat** — one rule / one comparison; compound
AND/OR logic belongs in a custom block, then pooled via HYBRID.

---

## Step 0 — One-time setup: ASK FOR THE SQX INSTALL FOLDER (mandatory)

Do this **once per machine**. If `catalog.json` already exists next to this skill, skip to Step 1.

> **`/sqx-setup` does this step for all four skills at once**; `/sqx-doctor` reports health.

**Shared install path — check first.** All four sqx-lab skills share one stored SQX folder:
`~/.sqx-lab/sqx-install.txt` (override the directory with `SQX_LAB_HOME`) — outside the plugin
folder, so a plugin update doesn't wipe it. Written automatically after the first successful
bootstrap of *any* sqx-lab skill. If it exists, `python engine/bootstrap.py` with **no arguments**
uses it — tell the user which folder is being used and only re-ask if they say it's wrong (then
re-run with `--install "<corrected folder>"`, which updates the stored path). A path is stored
only after it validates as a real SQX install, so a wrong folder can't break the other skills.

**On first use (no stored path) you MUST ask the user where StrategyQuant X is installed** — the
top-level folder (e.g. `C:\StrategyQuantX144` or `D:\SQX_…`, the one with `internal/` and `user/`).
Do not silently auto-detect. Then:

```
python engine/bootstrap.py --install "<the folder the user gave>"
```

Optional help to answer: `python engine/discover.py` *suggests* installs found on this machine —
show the candidate(s), have the user confirm. (`--auto` auto-picks without asking — CLI convenience
only, not the skill's setup path.)

This writes `catalog.json` (machine) and `catalog.md` (human). **Read `catalog.md`** — it lists:
- **⭐ YOUR custom blocks**, by `Condition / category` and `Price level / category` — the HYBRID
  pool source (every `CBlock_*` you can re-export, with its opposite).
- **inline rule templates** (simpleRules booleans) and **inline value atoms** — the INLINE source.

This is your source of truth for what THIS install can pool. Consult it; do not guess key names.

## Step 1 — Clarify (only what you cannot infer)

- **Theme / what the pool is for** (a rule pool, a level pool, "my breakout blocks", a paper).
- **`Condition` or `Value`?** Condition = boolean rule pool. Value = price/number pool (levels,
  stops, comparison operands). Inferable from the theme.
- **Hybrid or inline?** Pool *existing blocks* → hybrid. Pool *fresh atoms* → inline. "Group my X
  blocks" = hybrid; "a pool of EMA/RSI/ATR lines" = inline. Inferable.
- **How many items?** Default 5–8 (a pool, not a kitchen sink).
- **Which knobs to optimize vs freeze?** Default: optimize the numeric knobs — period/double
  AND int knobs (every custom-block `#IntN#`, session hours) — with `randomValue="default"`;
  freeze only if the user wants a fixed value. A misspelled optimize key, or one targeting a
  data/combo/shift param, raises ValueError (never silently dropped). `number(v,
  optimize="lo:hi:step")` makes a constant threshold a knob too.

If given a paper/URL, extract the rules yourself.

## Step 2 — Spec in plain English BEFORE writing XML

For each group, state in chat: name · `type` · category · mode (hybrid/inline) · the items
(each block key or atom + rule), with which knobs are optimized. Confirm every key exists in
`catalog.md`. Let the user approve or redirect before any XML. **Cheapest place to catch a wrong
pool.**

## Step 3 — Key check (against the catalog, not memory)

```python
import json; from pathlib import Path
from engine.groups import load_catalog
meta, T, B = load_catalog("catalog.json")
"CBlock_SuperTrendLevel" in B      # hybrid: is this block here?
"HMAFalling" in T                  # inline: is this rule/atom here?
```
A key not in the catalog isn't in this build — pick an equivalent that is, and say so. Do not
invent keys. Check an item's `returnType` matches the group `type` (Condition→boolean,
Value→price/number).

## Step 4 — Generate via a script

Copy `examples/gen_group_example.py`, change the pools, write to `<name>.xml`. Core API:

```python
from engine.groups import (load_catalog, inline_item, is_greater, is_lower, crosses_above,
    number, hybrid_ref, make_group, wrap_groups)
_, T, B = load_catalog("catalog.json")

# HYBRID — pool existing blocks by reference (frozen knobs by default; optimize=… to randomize)
trend = make_group("TrendUP", "Condition",
    [hybrid_ref(B[k]) for k in ("CBlock_EMACrossUp_Trend", "CBlock_SuperTrendFlipUp_Trend")],
    category="Trend")

# INLINE — fresh rules / comparisons (native keys; optimize with "default" or "lo:hi:step")
filt = make_group("Filters", "Condition", [
    inline_item(T["HMAFalling"]),                                  # frozen
    inline_item(T["MomRising"], optimize={"#Period#": "10:60:5"}), # override range
    is_greater(inline_item(T["Close"]), inline_item(T["EMA"], optimize={"#Period#": "default"})),
    is_lower(inline_item(T["RSI"]), number("30")),                 # vs a constant level
], category="Filters")

xml = wrap_groups([trend, filt])
```
Conventions (the engine handles most):
- **Optimizer model:** `optimize={key: "default"}` → randomize over the atom's own min/max/step;
  `{key: "10:60:5"}` → an explicit range; omit a key → **frozen**. Hybrid blocks are frozen by
  default (pass `hybrid_ref(B[k], optimize={"#Int2#": "default"})` to randomize one).
- **Flat items only** — no `and_op`/`or_op`. Compound logic → a custom block → `hybrid_ref`.
- **Type contract** — a `Condition` group's items must be boolean; a `Value` group's price/number.
- **`status`/`action`** are emitted by default; pass `status=None, action=None` to omit (a UI-made
  group does). Each group gets a fresh UUID automatically.

## Step 5 — Validate (must pass before you declare done)

```
python engine/validate.py <name>.xml                          # hybrids resolved vs the stored install (LIVE customBlocks.xml)
python engine/validate.py <name>.xml --catalog catalog.json   # fallback source when no install is stored
```
All 8 checks must pass — a dead hybrid pool (a `CBlock_*` key the live install doesn't have),
an empty file, an empty group, or an empty operator operand is a FAILURE, not a warning.
Warnings are allowed (a frozen knob or a cross-file `oppositeBlockKey` is fine). Don't report
success until they pass.

## Step 6 — Summarize + hand off

Give the user a short table (group → type → items) and tell them to import `<name>.xml` into
AlgoWizard (random/block groups → import). Note anything to verify (a brand-new block key, an
inline custom-snippet rule).

## Step 7 — User imports, reports failures

Fix the specific group/item; don't rewrite the whole set. A hybrid item that won't resolve usually
means its `CBlock_*` isn't imported in that install — check the block exists first.

## When to push back

- 20+ items in one group → split into two themed pools.
- A key not in `catalog.json` → it isn't in their build; propose an equivalent that is.
- A request to put AND/OR logic in a group item → that's a custom block; build it there, then pool.
- "Long and short variants of this group" → that's two groups (pools are unpaired); or one pool of
  hybrid blocks whose members carry their own `oppositeBlockKey`.

## Reference

- `catalog.md` — what THIS install can pool (read it first).
- `reference/groups.md` — the random-group XML format, condensed.
- `examples/gen_group_example.py` — the copyable template (hybrid + inline, Condition + Value).
- `engine/` — `discover.py` (find install) · `bootstrap.py` (install → catalog) · `groups.py`
  (emit items + groups) · `validate.py` (lint before import).
- `evals/run_evals.py` — deterministic self-test (19 cases: regenerate the example set, re-validate a
  real export, assert the guardrails + Tier-1 audit fixes fire — see `evals/test_tier1.py`) against
  your bootstrapped catalog: `python evals/run_evals.py`.
