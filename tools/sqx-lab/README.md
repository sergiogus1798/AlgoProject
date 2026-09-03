# ih-claude-code

Claude Code plugins and skills for authoring **StrategyQuant X / AlgoWizard (build-144)** artifacts. Everything is portable and install-derived: each skill bootstraps a per-install catalog from the SQX install you point it at, then emits a validated artifact. Machine-specific files (`catalog.*`, `sqx-install.txt`, `scaffold.xml`, `container`) are gitignored — they regenerate on bootstrap.

## Contents

| Where | What |
|---|---|
| [`plugins/sqx-lab/`](plugins/sqx-lab/) | **SQX Authoring Toolkit plugin** — the four authoring skills (blocks → groups → templates → projects). The current, recommended way to use them. |
| [`sqx-strategy-oracle/`](sqx-strategy-oracle/) | **Standalone strategy-builder plugin** — the `sqx-strategy` skill + `sqx-builder` agent (Oracle build: live-load verification via a headless backtest oracle). Turns a natural-language trading idea into a finished, ready-to-backtest `.sqx`. See its [`README.md`](sqx-strategy-oracle/README.md) and [`TUTORIAL.md`](sqx-strategy-oracle/TUTORIAL.md). |
| [`skills/`](skills/) | **Legacy standalone copies** of the four authoring skills, for manual drop-in to `.claude/skills/`. Superseded by the `sqx-lab` plugin above — prefer the plugin; these are kept for reference and manual installs. |

---

# SQX Authoring Toolkit (`sqx-lab` plugin)

A Claude Code plugin bundling the four **portable, install-derived** skills that author the reusable vocabulary a StrategyQuant X / AlgoWizard (build-144) strategy builder samples from. Each skill points at *your own* SQX install, derives a per-install catalog, and validates its output before import.

## Skills

| Skill | Authors | Composes into |
|---|---|---|
| `sqx-custom-block` | atomic trading rules — Condition blocks (true/false) + Price-level blocks (return a price: stop/target/band) | groups |
| `sqx-random-group` | flat alternative pools the builder samples (Condition + Value; hybrid re-export or inline atoms) | templates |
| `sqx-strategy-template` | full `.sqx` strategies with optimizable holes, bound to your install's clean groups | projects |
| `sqx-strategy-project` | build projects (`project.cfx`) that wire templates in as build tasks | — |

The chain: **block → group → template → project.** (The finished-strategy *builder* — `sqx-strategy` — lives in the separate `sqx-strategy-oracle` plugin above.)

## Layout

```
ih-claude-code/
├── .claude-plugin/marketplace.json     # marketplace for the sqx-lab plugin
├── plugins/sqx-lab/
│   ├── .claude-plugin/plugin.json
│   ├── sqx_common.py                   # shared install validation + per-machine state
│   ├── doctor.py                       # /sqx-doctor health check
│   ├── commands/                       # /sqx-setup · /sqx-doctor
│   └── skills/
│       ├── sqx-custom-block/
│       ├── sqx-random-group/
│       ├── sqx-strategy-template/
│       └── sqx-strategy-project/
├── sqx-strategy-oracle/                # standalone plugin (own marketplace inside)
└── skills/                             # legacy standalone skill copies
```

## Install

Clone this repository, add the cloned folder as a plugin marketplace, then install the
plugin and restart Claude Code:

```
git clone https://github.com/strategyquantsro/ih-claude-code.git sqx-lab
/plugin marketplace add /absolute/path/to/sqx-lab
/plugin install sqx-lab@sqx-lab
```

To also install the strategy-builder plugin, add `sqx-strategy-oracle/` as a second
marketplace (it carries its own `.claude-plugin/marketplace.json`) — see its README.

## Per-install setup

```
/sqx-setup        # point sqx-lab at your SQX install + bootstrap all four skills
/sqx-doctor       # health check: install, Python, catalogs, chain integrity
```

`/sqx-setup` is the whole first run. It asks for your StrategyQuant X folder once — the
top-level one containing `internal/` and `user/` — bootstraps all four skills against it,
and reports what it found. To point at a different install later, run it again.

**State lives outside the plugin.** The confirmed install path is stored in
`~/.sqx-lab/sqx-install.txt` (override the directory with `SQX_LAB_HOME`), so a plugin
update or reinstall no longer wipes it; a pre-1.2 path at the plugin root is migrated
automatically. A path is only ever stored **after** it validates as a real SQX install, so
pointing one skill at the wrong folder can no longer silently break the other three.

Each skill also derives a `catalog.*` from your install (gitignored — never committed).
Catalogs are written next to their own skill no matter which directory you run from, and
they *do* live in the plugin copy — so after a plugin update, re-run `/sqx-setup` to
rebuild all four (seconds).

Run `/sqx-doctor` whenever something behaves oddly. It reports whether the
block → group → template → project chain is actually intact, and — importantly — whether
any of your random groups are **broken** (referencing custom blocks that aren't in the
install). A broken *Value* group silently disables every build-confirmed strategy shape;
the doctor names it and walks through the repair.
