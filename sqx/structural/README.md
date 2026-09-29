# sqx/structural — rewrite a strategy's rules, not its values

Encargo 12, the factory and the run. `sqx/variants/` moves parameter values and refuses anything
else; this folder edits the **logic**: one entry condition deleted (D1, ablation) or the order
direction flipped on the same entries (D2, inversion). The statistical half — which condition carries
the edge — is `studies/readings/structure/`. Workflow step 23, per surviving strategy, after the
conditional map (22) and before the ATR stop (24).

Same three boundaries as the variant factory: **decide** (`plan.py`), **write** (`logic.py` +
`make.write`), **read back** (`make.read_back`, and `keep.py` after SQX ran). The id stamp, the two
name fields and the `<Fingerprint>` removal are `sqx.variants.build.rewrite.variant`, reused as is.

| file | what it does | run it | in → out |
|---|---|---|---|
| `logic.py` | Text substitution on `strategy_Portfolio.xml`: the entry conditions as their signal's direct children, one deleted, or every `#Direction#` negated and every side word swapped | imported | XML → XML |
| `plan.py` | Per mother: the identity rebuild, one ablation per condition of a signal with two or more, the inversion; and what each file must hold once written | imported | mothers → rows |
| `make.py` | The command: writes the batch, reads every file back and refuses one that is not the plan | `python3 -m sqx.structural.make --mothers <dir> --out <batch>` | `.sqx` → `sqx/` + `structure.parquet` |
| `keep.py` | After `sqx.variants.execute`: copies the retested files out of the install and checks each still carries its edit | `python3 -m sqx.structural.keep --work <batch>` | databanks → `retested/` + `retained.parquet` |

## The run is not here

`python3 -m sqx.variants.execute --work <batch> --project <P>` retests the batch on the custodian's
three WFC legs, one job, and stops it. `sqx.export.export_retest` then exports the three legs' trades
with one SQX start (`--databank` repeated), tagged `--batch structure` so step 24's stop-grid export
into the same databanks the same day does not overwrite these (OPEN #74; `studies.readings.structure.inputs.latest`
looks for that tag first). The whole sequence, with a real output, is `docs/manual/06-lecturas.pdf` (cap. 51-estructura).

## What was measured, 2026-09-26 (USDJPY `Strategy 23.1.53`, knowhow/sqx-format/rewriting-strategy-logic.md)

- **SQX runs a rewritten rule as written.** Deleting a `<Block>` of the entry AND: loaded, retested,
  the retested file carries the edit byte for byte. An AND left with one block is accepted.
- **Flipping `#Direction#` and swapping the side words inverts the strategy**: 694 of 694 trades
  back at the same instants, same size, opposite side; per-trade gross correlation −1.0000.
- **A retest drops the `<!--variant_id-->` stamp.** The retested XML is the fabricated one minus
  that comment. The join key after a run is the file name, `(N)` stripped — `read_back` uses it.
- **An identical backtest can be a redundant condition, not an ignored edit.** Deleting
  `MABarClosesAbove` returned the mother trade for trade; the retested file had lost the block, and
  QQE(14) crossing 57.72 never happens on a close below EMA(50) in 2008–2022. `keep.py` is what
  tells the two apart.

## Limits, on purpose

- Only **entry** signals are ablated. Exit signals are another test, and this corpus has none.
- A signal with a single condition gets no ablation: deleting it leaves no entry rule.
- `logic.invert` refuses a strategy whose entries carry a stop, a target, a trailing or a
  break-even: a flipped order is a mirror only without them. At step 23 there are none; step 24
  adds the ATR stop, after this.
- Orphan variables stay declared after an ablation (the deleted block's parameters). SQX loads the
  file with them; nothing reads them.
