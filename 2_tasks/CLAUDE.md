# 2_tasks — population analysis

Everything about a whole databank or a whole build: thousands of strategies at once. One strategy at
a time belongs in `3_strategies/`.

`extract/` pulls data into the data root, `analysis/` does the maths, `reports/` renders it.
Extraction never re-runs by accident: an export is dated, immutable, and carries a `manifest.json`.
Check `~/Desktop/AlgoData/INDEX.md` for what already exists before exporting anything again.

## Traps that have already produced wrong answers

- **Deduplicate on the exported trade list**, not on the strategy name and not on the XML hash. 45 of
  231 strategies had byte-identical trades under different hashes.
- **A strategy's stored result covers whatever window it was last retested over**, which is not
  necessarily the window you are studying. Check before pooling.
- **Two structurally different populations can share one databank.** Any pooled exit statistic hides
  that. Split before you average.
- **IS metrics are not OOS metrics.** The column suffixes `(IS)` / `(OOS)` / `(Full)` come from the
  view's sample types; never report one as the other.
- Multiple-testing is the default condition here, not an edge case: these strategies were selected by
  searching. Say what the search space was before claiming an edge.

Details in `knowhow/04-export.md`.
