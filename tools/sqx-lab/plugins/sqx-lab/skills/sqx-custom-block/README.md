# sqx-custom-block — a Claude Code skill for authoring SQX/AlgoWizard custom blocks

Describe a trading rule in plain English; get an importable AlgoWizard custom-block XML,
validated, built from **your own** StrategyQuant install's indicators. Works on any SQX 14x
build because it discovers your indicator vocabulary instead of hardcoding one.

## Install

Copy the `sqx-custom-block/` folder into your Claude Code skills directory:

- Global (all projects): `~/.claude/skills/sqx-custom-block/`
- One project: `<project>/.claude/skills/sqx-custom-block/`

No dependencies — Python 3.8+ standard library only.

## One-time setup: build your catalog

The skill learns what your build can do by reading your SQX install **once**. You point it at
your install folder — you don't hunt for individual files. **Name your install folder
explicitly** (the top-level one, e.g. `C:\StrategyQuantX144`, that contains `internal/` and
`user/`):

```
cd ~/.claude/skills/sqx-custom-block
python engine/bootstrap.py --install "C:\StrategyQuantX144"   # builds the catalog
```
Not sure of the path? Let discovery suggest candidates, then confirm which one is yours:
```
python engine/discover.py            # lists StrategyQuant X installs it can find
python engine/bootstrap.py --install "<the folder you confirmed>"
```
When Claude runs this skill it will **ask you for your StrategyQuant X folder** on first use —
that is by design. (`--auto` auto-picks without asking and is for manual CLI use only.)
From the install root it auto-resolves four sources, so **every custom indicator you have is
included**, whatever state it's in:
- `…/branding/global/config.xml` → native built-ins **+ your own custom indicators registered in
  AlgoWizard** (marked `customSnippet="true"`, surfaced as **YOUR custom indicators**). This is
  the primary, machine-independent way your indicators are found — it works **with or without the
  `.java` source on disk**, and is what fixes "it didn't find my indicator" on another computer.
- `…/user/settings/customBlocks.xml` → custom indicators you've used in a block (proven)
- `…/user/extend/Snippets/.../Indicators/*/*.java` → indicators you've **coded** — read straight
  from the Java source (supplementary; also catches ones coded but not yet registered)
- `…/branding/global/UserCustomIndicators.xml` → registry of custom indicators (synthesized)

(Manual override: `python engine/bootstrap.py /path/to/config.xml --export /path/to/customBlocksExport.xml`.)

This writes:
- `catalog.json` — machine catalog used to build blocks
- `catalog.md` — opens with a **⭐ YOUR custom indicators** section (your own indicators listed
  by name), then every indicator you can use (with midlines, optimizer knobs, and warnings;
  `✦` marks one of your custom indicators, `✎` a synthesized one)

Claude runs this for you the first time you ask for a block, if you tell it where `config.xml` is.

**Your own indicators are first-class.** Any custom indicator you've registered in AlgoWizard is
recognised straight from `config.xml` (the `customSnippet` marker) and used directly — no Java
source required. If one is also in a block you've exported, that proven schema is used. If it's
brand-new (never registered, never in a block), the skill synthesizes it from your install
registry — and for guaranteed fidelity you can drop it into one throwaway block, export, and
re-run setup to upgrade it from synthesized to proven.

## Use

Just ask, in Claude Code:

> "Make me a custom block that goes long when RSI crosses up through 30 and short when it
> crosses down through 70."

Claude will: confirm the spec → check the indicators exist in your catalog → generate the
XML → validate it (7 checks) → tell you what to import.

Or ask for **ideas** instead of a specific rule:

> "What momentum blocks could I build that I don't already have?"

Claude spawns a research agent that proposes candidate blocks **grounded in your catalog**
(only indicators you actually have), gates them so nothing un-buildable gets through, shows you
a ranked list with sources, and authors the ones you pick.

Then in AlgoWizard: **Custom Blocks → import** the generated `.xml`.

## What's in here

```
sqx-custom-block/
├── SKILL.md                  the workflow Claude follows
├── engine/
│   ├── discover.py           find the SQX install + its 3 catalog files
│   ├── bootstrap.py          install -> catalog.json / catalog.md (--auto / --install)
│   ├── emit.py               Catalog.atom(): a catalog entry -> block-ready XML
│   ├── grammar.py            operators, arithmetic, the CBlock_* wrapper (build-stable)
│   ├── check_specs.py        gate researched specs vs the catalog (no phantoms/talib)
│   └── validate.py           7-check linter (run before every import)
├── examples/
│   └── gen_example.py        a worked RSI pair — the template to copy
└── reference/
    ├── lessons.md            the hard-won rules and why they exist
    ├── grammar.md            the block XML format, condensed
    └── research-prompt.md    prompt for the catalog-aware "block researcher" subagent
```

## Why it's portable

A native indicator in your `config.xml` is already ~90% of a usable block atom — the
transformation into a block-ready atom is mechanical and identical for every indicator.
The skill copies *your* schema rather than assuming one, so it's correct for your build by
construction. Operators and the block wrapper don't change between builds, so those ship as
proven code. The result: another user runs `bootstrap` against their install and authors
validated blocks with their indicators — no edits to the engine.

## Manual use (without Claude)

```
python engine/bootstrap.py /path/to/config.xml          # build catalog
cp examples/gen_example.py mygen.py                       # edit the block list
python mygen.py catalog.json my_blocks.xml                # generate
python engine/validate.py my_blocks.xml --catalog catalog.json   # check
```
