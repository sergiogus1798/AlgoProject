# Local changes to the vendor's sqx-lab 1.2.0

A new vendor version unzipped over `tools/sqx-lab/` erases all of this. `bin/sqx-lab-install.sh`
re-applies the overlays by itself and warns when a code patch below is missing; re-apply those by
hand, or check whether the new version fixed them.

## Code patches — each marked `LOCAL PATCH` in the file

| file | what was wrong on this install | 🔬 |
|---|---|---|
| `plugins/sqx-lab/skills/sqx-random-group/engine/groups.py` (`hybrid_ref`) | build 144's `customBlocks.xml` stores no `categoryType`/`help`/`strategyType` on any `CBlock_`, but every group item SQX writes carries them; copying the tag verbatim emitted a reference SQX never produces. Eval `hybrid_reexport_shape` failed | 2026-09-25, evals 18/19 → 19/19 |
| `plugins/sqx-lab/skills/sqx-strategy-project/engine/generate.py` (`verify`) | required five system databanks; a headless worker's stock project carries four (no `Existing portfolio`) | 2026-09-25 |

`sqx-strategy-project` is **retired** (owner, 2026-09-25): it clones any project of the install and
deploys into it, against hard rule 10, and six more of its evals fail here (MTF wiring, symbol swap,
acceptance attribute order). `sqx.projects.builder` does that job from the frozen donor. The
installer no longer links it; its catalog is still built because `/sqx-doctor` reads it.

## Overlays — `overlays/<skill>.md`

The project's own rules, inserted by the installer at the top of each wired `SKILL.md`, between
`<!-- ALGOPROJECT OVERLAY -->` markers. Edit the overlay here, never inside the vendor file.
