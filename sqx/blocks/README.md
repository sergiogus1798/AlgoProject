# sqx/blocks — custom blocks into an install

| file | what it does | run it | in → out |
|---|---|---|---|
| `install.py` | Add or replace custom blocks in a stopped install's `customBlocks.xml` | `python3 -m sqx.blocks.install <blocks.xml> [--role conductor]` | an XML of `<Item key="CBlock_…">` → the install's store, plus a dated backup |
| `taxonomy.py` | Refresh `taxonomy.yaml` — every block the builder can sample, ready to label by archetype — keeping every label already written | `python3 -m sqx.blocks.taxonomy [--role master]` | the install's three XML files + a donor's Build task → 767 rows in 83 categories |
| `taxonomy_discover.py` | Read the builder's reachable blocks off an install and a donor's Build task — used by `taxonomy.py`, not run on its own | — | a donor's Build task + a `vocabulary()` → block keys, roles and rows |
| `palette.py` | The palette library: named block selections, each a family plus what it changes, resolved against the taxonomy | `python3 -m sqx.blocks.palette [NAME]` | a palette + the taxonomy → a switch per block |

**No GUI import is needed.** `customBlocks.xml` is the store itself, and `sqcli` never rewrites it
(measured: `knowhow/authoring/headless-authoring-chain.md`). The GUI does, so the tool refuses to write while the
install's port answers — a write into a running instance is undone on exit, silently.

A key already present is **replaced in place**, never appended a second time: SQX reads the first
match, so a duplicate is invisible until a build picks the wrong one.

The authored XML does not live here. It lives beside the template that needs it, in
`AlgoData/templates/library/<name>/deps/`, so the template folder stays self-contained and installs
on any SQX unchanged.

## taxonomy.yaml

The labels are the point and they are **not** derived: `archetypes` is a weight per family
(`breakout`, `mean_reversion`, `trend`) that somebody — a person or a labelling agent — puts there.
Everything else in the file is read back from the install on each refresh and overwritten.

Only the **767 blocks the builder can actually sample** are here, taken from a Build task's
`<BuildingBlocks>`. The 253 natives that appear in no role — the actions, the maths functions, the
158 `talib_*` — are real vocabulary and unreachable from generation, so labelling them would be
labelling something no palette can ever switch.

⚠️ A palette built from these labels reaches a template's **free** holes only. A hole bound to a
random group samples that group and ignores the switches entirely — measured, `knowhow/authoring/builder-block-switches.md`.
Narrowing a bound hole means choosing or authoring the group.
