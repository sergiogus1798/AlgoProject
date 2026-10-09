---
name: rebuild-sister
description: Write again the .sqx of a step-12 scaled sister (a stored strategy moved to M15, H1, H4…) from the strategy store — the store keeps the mother's file and each sister's parameters, never the sister's file. Use when the owner asks to rebuild, recover, reconstruct or load a scaled version of a saved strategy, or wants the .sqx of a strategy «en otro timeframe» that step 12 already made.
---

# /rebuild-sister

The store (`AlgoData/store/<cell>/<identity>/`) keeps a sister as a row of `scaling.parquet` inside
`hermanas.<day>.zip`: every parameter written and what it was, the ATR ratio used, the batch index
and the identity of the file fabricated then. The scaling is deterministic, so the file is made
again from the mother's `strategy.sqx` — nothing here touches SQX.

1. **Which mother.** The owner names a strategy; find its identity with
   `python3 -m core.store list | grep '<name>'`. More than one hit (the same name in two runs of
   a cell) → ask which (rule 11).
2. **Rebuild**, into a folder outside the repo (rule 7):
   `python3 -m sqx.variants.rebuild <identity> [M15 H1 H4…] --out <folder>` — no timeframe means
   every sister the store keeps of that mother.
3. **Read the line per sister.** `igual` = same parameters and the same identity as the file step
   12 fabricated. `DISTINTA` (exit 1) = the scaling rules or `sqx/variants/config.yaml` changed
   since: report the lines it prints and stop — the stored row's `param_*` columns still say what
   the sister was; do not hand the owner the new file as if it were the old one.
4. To see a sister's parameters without rebuilding: the `scaling.parquet` member of
   `hermanas.<day>.zip` (`param_<k>` written, `was_<k>` the mother's).

The identity SQX gave the sister when it retested it differs from the fabricated file's
(`knowhow/sqx-format/fabricated-variant-identity-differs-from-retest.md`): its trades in
`operaciones.CrossTF_<TF>.<day>.zip` are filed under the sister's NAME, `<mother>_Scaled<TF>`.

A timeframe step 12 never made is not a rebuild: that is `/crosstf`.
