---
q: Why does Benjamini-Hochberg raise, and where must NaN p-values be filtered?
kw: fdr nan p-value, benjamini hochberg ValueError, engines/inference/fdr.py, gate, isOos many, filters report
tag: 🔬  date: 2026-10-04
---
# `engines/inference/fdr.py` raises on a NaN p-value — filter before, keep the rows
Callers drop NaN-p rows before the FDR and keep them in the output table: `gate`, `isOos/many.py`, `filters/report.py`.

## Evidence
2026-10-04 cleanup (`CALC_REVIEW.md`).
