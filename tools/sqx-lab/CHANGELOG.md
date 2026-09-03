# Changelog

## 1.2.0 — onboarding, self-healing, short shapes

### Setup no longer fails silently

`/sqx-setup` and `/sqx-doctor` are new. `/sqx-setup` asks for your StrategyQuant X folder
once and bootstraps all four skills; `/sqx-doctor` reports Python, install, per-skill
catalogs, and whether the block → group → template → project chain is actually usable.

Three bugs that made a wrong folder expensive:

- **`sqx-strategy-project` accepted any folder**, printed `0 projects / 0 templates` as if
  that were success, and then stored the bad path — silently breaking the other three
  skills. It now validates first and refuses.
- **`sqx-strategy-template` raised a bare `FileNotFoundError` traceback** for the same
  mistake. All four skills now share one error format: what's wrong, the path it looked
  for, and the command that fixes it.
- **The install path is only stored after it validates**, so one skill can no longer
  poison the others.

### State survives plugin updates

The shared install path moved from the plugin's own (version-scoped) folder to
`~/.sqx-lab/sqx-install.txt` — override with `SQX_LAB_HOME`. A pre-1.2 path is migrated
automatically on first read. Catalogs still live beside their skill; re-run `/sqx-setup`
after an update to rebuild them.

### Catalogs stop landing in your project

`--out-dir` defaulted to `.`, so bootstrapping from a project directory dropped a ~500 KB
`catalog.json` into whatever repo you were in. It now defaults to the skill folder
regardless of where the command runs from.

### Broken random groups are diagnosed and repairable

A group referencing `CBlock_*` blocks that aren't in the install was excluded from every
design, silently and permanently. `discover.py` now emits a **`repair_manifest`** carrying
each missing block's key, type, and AlgoWizard rule text — a work order the
`sqx-custom-block` skill consumes in its new **Repair mode**. It also warns explicitly
when there is no clean Value group, because that alone disables every build-confirmed
strategy shape.

### Short-only strategy shapes

`stop_short`, `mtf_filter_short`, `market_short` — 11 shapes to 14.

`proto_short_fleet.py` was rewritten. The old transform kept the mirror
(`generate="opposite"`) signal and fired the entry off it, so the template traded each
pooled block's `oppositeBlockKey`. Non-directional blocks — session/time filters — carry
`CBlock_null` and have no opposite, so any pool containing one silently broke. The new
transform empties the mirror signal and fires on the **primary** signal with
`#Direction#=-1`, matching a hand-corrected working reference set.

**Design contract:** a short template trades its chosen groups directly. Nothing mirrors
them for you, so a short design must name genuinely bearish pools — including a **lower**
level pool for the sell-stop. Documented in `SKILL.md` and `research_agent.md`.

Status is ⏳ pending build-confirm: the architecture matches a working reference, but no
*engine-generated* short template has been through an AlgoWizard Build yet.

### Evals

- **`sqx-strategy-template` now ships a fixture install** (`evals/fixtures/`) and uses it
  by default. The harness previously read the user's real catalog and SKIPped whenever it
  lacked clean groups — the normal state of a fresh install — so the only automated check
  on the most complex generator in the toolkit essentially never ran. `--install <path>`
  still exercises a real install. Groups are read in memory; the harness never writes
  `engine/catalog.json`.
- **A SKIP is no longer green.** Exit `2` = did not run, distinct from `0` pass and `1`
  fail, with a banner naming what's missing.
- **`sqx-strategy-project` E3 fixed.** It compared each cloned task against `clone_task`
  alone while the engine also runs `ensure_mtf_charts`, so it failed on any MTF template.
  The eval was stale, not the engine. 10/11 → 11/11, plus three `DeprecationWarning`s
  silenced.
- **Short-architecture invariants are asserted** — mirror empty, `#Direction#=-1`, entry
  on the primary signal — so the fixed transform cannot silently regress.

### Docs

- `allowed-tools` was `Bash(python engine/*)`, which didn't even permit running the
  generator scripts the skills write in Step 4. Now matches actual usage.
- Documented five `sqx-strategy-project` engine features that existed in code with zero
  mentions in `SKILL.md`: `generation.databank_cap` and `generation.acceptance`
  (survivorship control), `trading.friday_exit`, and `analysis_tasks` /
  `build_analysis_task`.

### Known gaps

- Catalog location is still inconsistent (`sqx-custom-block` / `sqx-random-group` write to
  the skill root, the other two to `engine/`). Tolerated by `sqx_common.find_catalog()`.
- The repo still carries legacy standalone copies under `skills/` and a nested
  `sqx-strategy-oracle` marketplace.
- If `python` resolves to the Windows Store stub, failure happens before any plugin code
  runs. `/sqx-doctor` reports the interpreter in use.

## 1.1.0

Four authoring skills — `sqx-custom-block`, `sqx-random-group`, `sqx-strategy-template`,
`sqx-strategy-project` — as an installable plugin.
