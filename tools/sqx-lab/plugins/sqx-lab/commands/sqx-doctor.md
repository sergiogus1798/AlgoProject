---
description: Health check for sqx-lab — install, Python, catalogs, and whether the block→group→template→project chain is intact.
allowed-tools: Bash, Read
---

# sqx-lab doctor

Run the check:

```bash
python "${CLAUDE_PLUGIN_ROOT}/doctor.py"
```

Exit 0 = healthy. Exit 1 = the numbered fix list at the bottom is what to work through.

## How to read it to the user

Don't paste the raw output. Give them:

1. **One line of verdict** — healthy, or the single most important thing that's broken.
2. **The state of the chain**, because that's what decides whether they can build
   anything at all:
   - `clean Value groups: 0` is the serious one — `stop`, `stop_long` and `mtf_filter`
     are the *build-confirmed* shapes and every one of them needs a price pool. With
     zero Value groups the user can only generate market-entry shapes, and the template
     skill's evals will just print `SKIP`.
   - `clean Condition groups < 2` means most shapes can't be filled (they need a filter
     **and** a trigger).
3. **The numbered fixes**, in the doctor's order — it already ranks them.

## Repairing broken groups

A broken group references `CBlock_*` blocks that aren't in this install's
`customBlocks.xml` — typically the group was imported (or survived a reinstall) but its
blocks weren't. The group is then excluded from every design, silently, forever.

The fix is real work but it's mechanical, and the material is already there:

```bash
python -c "import json;d=json.load(open(r'${CLAUDE_PLUGIN_ROOT}/skills/sqx-strategy-template/engine/catalog.json',encoding='utf-8'));print(json.dumps(d['repair_manifest'],indent=2,ensure_ascii=False))"
```

Every entry carries the missing block's `key`, its `block_type` (Condition or Price
level), and `rule` — AlgoWizard's own display text for it, e.g. `Close > HighD[1]` or
`(Close - VWAP) > #Double4# * ATR`. That is enough for the **`sqx-custom-block`** skill
to re-author them.

Hand it the manifest and ask it to rebuild the blocks. Then:

1. import the emitted XML into AlgoWizard (Custom Blocks → import),
2. re-run `python "${CLAUDE_PLUGIN_ROOT}/skills/sqx-strategy-template/engine/discover.py"`,
3. the group flips to CLEAN and the shapes it gated become available.

**Prioritise a broken *Value* group** — repairing one unlocks every build-confirmed
shape at once.

Caveat worth stating plainly: `Price level` entries in the manifest often carry only a
name (`CBlock_PrevDayHigh`, `CBlock_KamaUpperBand`) rather than a full expression,
because AlgoWizard stores no display text for them. Those have to be re-derived from
the name and confirmed with the user before authoring — don't guess silently.
