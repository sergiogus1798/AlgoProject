# sqx-random-group — a Claude Code skill for authoring SQX/AlgoWizard random groups

Describe a pool — "a group of breakout triggers", "pool my trend blocks", "a group of EMA/ATR
levels" — and get an importable AlgoWizard random-group XML, validated, built from **your own**
StrategyQuant install. Works on any SQX 14x build: it discovers what you can pool instead of
hardcoding a vocabulary.

A random group is a **menu the strategy builder draws one item from per strategy**, for a single
slot (bound to a template's *Same condition* / *Same value* placeholder). This skill is the sibling
of `sqx-custom-block`: that one builds the blocks, this one pools them.

## Install

Copy the `sqx-random-group/` folder into your Claude Code skills directory:

- Global (all projects): `~/.claude/skills/sqx-random-group/`
- One project: `<project>/.claude/skills/sqx-random-group/`

No dependencies — Python 3.8+ standard library only.

## One-time setup: build your catalog

Point it at your SQX install folder **once** (the top-level one, with `internal/` and `user/`):

```
cd ~/.claude/skills/sqx-random-group
python engine/bootstrap.py --install "C:\StrategyQuantX144"
```
Not sure of the path? `python engine/discover.py` lists installs it finds; confirm which is yours.

This reads two sources and writes `catalog.json` (machine) + `catalog.md` (human):
- `…/branding/global/config.xml` → **inline** rule templates (simpleRules booleans) + value atoms.
- `…/user/settings/customBlocks.xml` → **your `CBlock_*` custom blocks**, poolable by reference
  (hybrid). `catalog.md` lists them by `Condition / category` and `Price level / category`.

## Use

Just ask, in Claude Code:

> "Make me a Condition group that pools my breakout blocks."
> "Build a Value group of EMA, KAMA and ATR-band levels."
> "Pool RSI<30, Momentum-rising and Close-above-EMA into a filter group."

Claude will: confirm the spec → check the keys exist in your catalog → generate the XML →
validate it (4 checks) → tell you what to import. Then in AlgoWizard: import the `.xml` into your
random/block groups.

## Two item modes

- **Hybrid** — re-export your existing custom blocks by reference (`CBlock_*`). The common case;
  most real 144 groups are a thin index into your block library.
- **Inline** — fresh items built from catalog atoms: a `simpleRules` boolean, a bare value atom,
  or one operator comparison (`Close > EMA`, `RSI < 30`).

Items are **flat** (one rule / one comparison). Compound AND/OR logic belongs in a custom block,
then pooled via hybrid.

## What's in here

```
sqx-random-group/
├── SKILL.md                 the workflow Claude follows
├── engine/
│   ├── discover.py          find the SQX install + its files
│   ├── bootstrap.py         install -> catalog.json / catalog.md
│   ├── groups.py            emit items (hybrid + inline) and <Group> wrappers
│   └── validate.py          4-check linter (run before every import)
├── examples/
│   └── gen_group_example.py a worked set — the template to copy
└── reference/
    └── groups.md            the random-group XML format, condensed
```

## Why it's portable

A `simpleRules`/indicator entry in your `config.xml` is already a usable item template, and your
`customBlocks.xml` already holds your blocks — the engine copies *your* schema rather than assuming
one, so it's correct for your build by construction. Operators and the group wrapper don't change
between builds, so those ship as proven code.

## Manual use (without Claude)

```
python engine/bootstrap.py --install "C:\StrategyQuantX144"   # build catalog
cp examples/gen_group_example.py mygen.py                       # edit the pools
python mygen.py catalog.json my_groups.xml                      # generate
python engine/validate.py my_groups.xml --catalog catalog.json  # check
```
