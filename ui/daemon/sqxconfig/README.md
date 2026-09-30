# ui/daemon/sqxconfig — the settings every new SQX project is built and tested with

Encargo 22 §8.2, plan 24 F9. Every input of SQX that `sqx/projects/` writes into a task, by test,
each in its own section: `assets/_build.yaml` (one section per top-level key — complexity, order
types, exits, money management, trading options, engine, databank, precision, crosschecks,
cross-market, CrossTF, MC Retest, WFC, SPP, WFM), then `_classes.yaml` (the two cost schemas), the
globals of `_policy.yaml` (`segments_default`, `swap`, `mc_retest`) and `_markets.yaml` read only.
The per-asset parts of those files (`segments.<SIM>`, the symbol files) stay in Activos.

**WFC and CSCV also show their study files** (owner, 2026-09-28: «faltan el número de variantes
máximo por madre, o las combinaciones del CSCV»). The `wfc` section is extended and a `cscv` section
follows it, each value carrying its own `file`: the SPP design that sizes each mother's batch
(`studies/breakage/spp/config.yaml` `design`, `n_target` being the cap), the factory's floor, seed,
grids and canaries (`sqx/variants/config.yaml` `minimum`, `design`, `canaries`), the trade floor and
split both studies read (`engines/variants/config.yaml`, shown in both sections), each study's own
`config.yaml`, and `cscv.blocks` from `ledger/thresholds.yaml` in place of its `ledger:` placeholder.
The factory's `build`/`execute`/`spp`/`crosstf` blocks are plumbing and stay out.

Owner, Q17 (2026-09-27): **editable**. A write goes through `core.assetwrite.set_value`, the only
writer of `assets/`, and lands as the line it changes — comments, quotes and one-line lists kept.
It applies to projects created from then on: nothing here touches an existing `project.cfx`.

**Imports from:** `core.assetwrite`, `core.assetyaml`, `core.assetdata`, and for the option lists
`sqx.projects.acceptance`, `sqx.projects.wfm`, `sqx.variants.scale`, and for WFC/CSCV
`engines.variants.panel`, `studies.optimisation.cscv.measure` · **Consumed by:**
`ui/daemon/routers.py` (router), `ui/desktop/sqxconfig/` (over HTTP)

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The package's one-line purpose | imported | — |
| `lists.py` | The fixed vocabularies themselves — precisions, engines, order types, cross-checks, money-management methods, commissions, swap types, weekdays, spreads — hand-copied from the donor and SQX's own settings page | imported | — → constant lists |
| `options.py` | Per value: its type, its fixed options (SQX's precisions and engines, the donor's order types and cross-checks, `sqx.variants.scale.MINUTES` for CrossTF, the spans a section may run on, the WFM enums) or why it is locked | imported | file, path, value → spec |
| `sections.py` | The four files as sections: every leaf with its spec and its comment, and each branch's comment (`groups`) | imported | assets/ → sections |
| `write.py` | One value checked against its spec and coerced to the form the file holds, then `assetwrite.set_value` | imported | file, path, value → written |
| `studies.py` | The study values of WFC and CSCV: which file and branch each section shows (`PARTS`), their spec (ranges, CSCV's rules/score/period, the split names from `engines.variants.panel`), and a `ledger:` placeholder turned into the threshold row's value and `why` | imported | study files → fields |
| `studywrite.py` | One study value written with `assetyaml` (comments kept, byte-identical round trip checked 2026-09-28); a number keeps its file's type (a count int, a share float), odd CSCV blocks and `min_levels > max_levels` refused, strata not summing 1 and a max of variants under the min only warned; a changed threshold stamped `set_by: dueño`, `set_on` today and a proposed `why` naming the old value (not nesting the old why); a `why` is written as typed text, never through YAML; `reload` asks the window to re-read after a stamp or a `batch` value, which both sections show | imported | file, path, value → written |
| `api.py` | `GET /api/sqxconfig`, `POST /api/sqxconfig/value` (422 with the reason on a bad value) | imported | request → JSON |

## Contracts and traps

- **A list is written in the style it had.** `set_value` with a plain Python list turns
  `H1: [H4, H12]` into a block of three lines; `write._seq` hands it a flow `CommentedSeq`, so
  changing one timeframe is a one-line diff.
- **A quoted `"true"` stays quoted.** `trading_options` carries SQX's booleans as strings;
  unquoted they would be YAML booleans and `tasksettings.set_params` would write `True`.
- **CrossTF's timeframes come from `sqx.variants.scale.MINUTES`, not `buildrules.TF_MINUTES`.**
  The build list has no H12 and has H2; the siblings CrossTF reads are rescaled by `scale`, which
  knows H12 and not H2. The owner's own example (M30, H1, H4, H12) needs the scale list.
- **A span touching a reserved segment is offered only to its consumers.** `oos2` appears in
  the dropdowns of `wfc` and `wfm` (its `reserved_for` names them) and nowhere else, which is
  what `sqx.projects.setups.span` would refuse anyway.
- **Only a listed leaf is written.** `write.set_field` refuses (422) any path that is not one of
  `assetyaml.leaves` — a branch such as `exits`, one item inside a list of values, a key the file
  lacks — because `set_value` would replace or create whatever sits there. A `choice` must be one
  of its options (type included), a `choices` a list of them without repeats, a number inside
  `lists.RANGES`.
- **Two values re-read past runs.** `crosstf.timeframes` and `wfc.tasks[].segment` carry `warn`:
  `studies/transfer/crossTF` and `studies/readings/structure` read them from the file at analysis
  time (`knowhow/eng/studies-reread-build-yaml.md`, OPEN.md §80).
- **The study files are not assets/.** `core.assetwrite` stays the only writer of `assets/`;
  `studywrite` writes the six study files through the same `assetyaml` round trip. The WFC and
  CSCV re-read those values when they read a batch, so every one of them but the factory's and
  the design's carries `warn`. `ledger/thresholds.yaml` says in its header that the window writes
  `cscv.blocks`: it is the one exception to «no module writes it».
- **The SQX lists are hand-copied** (2026-09-27, from `result2.js`), not read at run time.
- **Titles and databank names are locked.** They are contracts with the harvests
  (`studies/breakage/mcRetest/inputs/tasks.py`, `sqx/variants/`); a rename from here would break
  the analysis in silence. So are the WFM's `period_type`/`optimization_type` (fixed by the
  owner), the acceptance `conditions` lists (structures, not values) and `_classes.yaml`'s
  `fields`/`field`/`unit` (read by name in `core/assetdata.py`, `core/assets.py`,
  `core/assetwrite.py`).
