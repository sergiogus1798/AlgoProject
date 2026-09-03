# sqx-strategy-template — a Claude Code skill for authoring SQX/AlgoWizard strategy templates

Describe a trading idea — "breakouts only in the trend direction", "a session-filtered momentum
entry" — and get an importable AlgoWizard **strategy template** (`.sqx`), validated, built from
**your own** StrategyQuant install. Works on any SQX build-144 install: it discovers the random
groups you actually have instead of hardcoding a strategy.

Third in the suite: `sqx-custom-block` builds the rules, `sqx-random-group` pools them into groups,
**this skill wires those groups into a buildable strategy template.**

## The idea in one line

A SQX strategy is a typed expression program; a *template* is that program with typed **holes**
(`RandomCondition`/`RandomValue` → a random group). This skill never hand-writes strategy XML — the
type system alone can't tell you what will *build* (engine rules, identity wiring, mirror discipline
live outside the schema). Instead it transplants your chosen groups into a **build-confirmed
skeleton** and varies only the holes, so the result stays inside proven-valid territory.

## Install

Copy the `sqx-strategy-template/` folder into your Claude Code skills directory:

- Global (all projects): `~/.claude/skills/sqx-strategy-template/`
- One project: `<project>/.claude/skills/sqx-strategy-template/`

No dependencies — Python 3.8+ standard library only.

## One-time setup: discover your install's groups

Point it at your SQX install folder (the top-level one, with `internal/` and `user/`):

```
cd ~/.claude/skills/sqx-strategy-template
python engine/discover.py "C:\StrategyQuantX"
```

This writes `catalog.json` and prints the **clean** random groups you can wire:
- **Condition groups** → usable as filters or triggers,
- **Value groups** → usable as stop/limit price pools.

A group is *clean* iff every custom block it references exists in your install; broken groups are
excluded automatically. If you need a pool that isn't there, build it with `sqx-random-group` first.

## Use

Just ask, in Claude Code:

> "Design a trend-filtered breakout template from my install."
> "Make a session-gated momentum entry (no Fridays)."
> "Give me three thesis-driven breakout designs and build them."

Claude will: discover your groups → design (assign filter/trigger roles, write a falsifiable thesis)
→ generate the `.sqx` → self-validate → tell you what to import. Then in AlgoWizard: import the
`.sqx` and run a Build.

## Shapes

| Shape | Entry | Status |
|---|---|---|
| `stop` | pending stop (fills on a price level) | build-confirmed |
| `market` | immediate fill | validated, confirm on your install |
| `market_single` | immediate fill, one condition | validated, confirm on your install |
| `session_market` | market + a time gate (e.g. not Fridays) | validated, confirm on your install |

The short side mirrors automatically; the full exit stack (SL/PT/Trailing/BE/ExitAfterBars) is
already in every skeleton — the template only chooses which exits are optimizable.

New structure (limit, multi-timeframe, grid) is added the same way the blocks/groups skills grow:
derive a skeleton from a template your install already proves, build-confirm it once, then it
generates at scale. See `reference/strategy-grammar.md`.

## What's in here

```
sqx-strategy-template/
├── SKILL.md                  the workflow Claude follows
├── research_agent.md         the design-reasoning layer (roles, confluence, falsifiable thesis)
├── engine/
│   ├── discover.py           install -> catalog.json of clean groups
│   ├── generate.py           design spec -> .sqx (self-validating)
│   ├── proto_session_gate.py how a new shape is derived from a proven install template
│   └── skeletons/            the build-confirmed skeletons shapes transplant into
├── examples/
│   └── gen_template_example.py  a worked design->.sqx batch (the template to copy)
└── reference/
    └── strategy-grammar.md   what a SQX strategy/template IS — the abstract model + design space
```

## Why it's portable

The skeletons encode the proven build-144 entry/exit *structure*; the groups come from **your**
install at generate time (the `#Group#` holes are rebound to your groups' UUIDs). The engine copies
your install's reality rather than assuming one. Each new install/shape is still gated by one
build-confirm — the same earn-it-by-import loop as the rest of the suite.

## Manual use (without Claude)

```
python engine/discover.py "C:\StrategyQuantX"                 # build catalog of clean groups
cp examples/gen_template_example.py mygen.py              # edit the designs
python mygen.py                                           # generate .sqx into engine/out/
```
