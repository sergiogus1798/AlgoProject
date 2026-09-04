# tasks — population analysis

Everything about a whole databank or a whole build: thousands of strategies at once. One strategy at
a time belongs in `strategies/`.

Pulling data out of SQX lives in `sqx/export/`, since it needs the SQX driving code in
`core/exportdrv.py`; `extract/` here is reserved and empty (corrected 2026-09-04, it never held
code). `analysis/` does the maths, `reports/` renders it. Check `~/Desktop/AlgoData/INDEX.md` for
what already exists before exporting anything again.

## Two lifecycles, deliberately in separate trees

**`metrics/<project>/<databank>/metrics.csv` is the current export and there is only ever one.**
Refreshing it deletes what was there first, so "which CSV is the real one" cannot arise. Trade and
bar exports keep the old rule — `raw/<project>/<databank>/<date>/`, dated and immutable — because
they are large and slow and are cited by strategy-level work. The two must not share a directory:
one is overwritten and the other must never be.

**Reports accumulate.** `reports/<project>/<databank>/<date>/` holds the conclusions and nothing
deletes them — the CSV is reproducible from SQX, the reasoning is not.

```
python3 -m sqx.export.export_metrics --project XAUUSD --databank OOS   # refresh the CSV
python3 -m tasks.reports.is_oos      --project XAUUSD --databank OOS   # analyse it
```

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
