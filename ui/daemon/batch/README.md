# ui/daemon/batch — one mother's variant batch, build and oos1 only

What «Lote» draws: every variant of one mother's batch with its `param_*` values and its
`NetProfit (build)` and `NetProfit (oos1)`. Reads `metrics.parquet` of the batch folder the
optimisation runner would pick (`studies/run/where.batch`), nothing else.

**Imports from:** `core/datapaths`, `studies/run/where` ·
**Consumed by:** `ui/daemon/routers.py` (`ROUTER`) → `ui/desktop/batchview/`

| file | what it does | run it | in → out |
|---|---|---|---|
| `api.py` | The variant-batch routes: one mother's batch for the parallel coordinates, and whether it has one. | imported | request → JSON |
| `panel.py` | One mother's variant batch as the parallel-coordinates view draws it: build, oos1 and, when the batch has it, oos2. | imported | metrics.parquet → dict |

## Contracts and traps

- **oos2 for a human, sealed for an autonomous agent.** A human gets `NetProfit (oos2)` as a
  third outcome when the batch has it, and «Lote» offers it. The one-way door holds only under `ALGO_AUTONOMOUS=1` (`core.assetdata.enforced`):
  the batch file holds `oos2`, `ALL` and `oos1+oos2` columns (`ALL`
  includes oos2), and `panel.columns` drops every column whose name contains `oos2` or `ALL` from the
  pyarrow column list, so those values are never read into memory; `api.get_batch` then walks the
  whole answer and, should any key or text still name one (a project or parameter so named),
  refuses the answer entire rather than trimming it. `tests/test_ui_batch.py` asserts it on a real
  batch and on a synthetic file carrying every sealed spelling.
- **The strategy's name has two spellings.** SQX writes `Strategy 18.13.59`, the factory's folder
  `Strategy_18.13.59` and the pipeline's `Strategy_18-13-59`; either form is accepted.
- **Two batches of one mother are refused, not chosen** — the same sentence the batch studies
  give (`studies/run/where.batch`).
- **A parameter with one value is not an axis**: it goes to `fixed` and to the note.
- **The mother is the row with `origin` true** (`P00000`, stratum `origin`, `sqx/variants/README.md`);
  canaries and inert pairs are drawn like any variant, their stratum shown on hover.
