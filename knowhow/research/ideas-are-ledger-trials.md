---
q: do the ideas spent, the ideaExpert's hypotheses or the market profile's tests count in the ledger's N, deflated Sharpe trials of a cell, ideas_spent hypotheses, long and short share a count, accumulated extra, N búsquedas + K hipótesis
tag: 🔬  date: 2026-10-02  see: research/pooling-moments
---
# A study's N is its scored candidates plus the hypotheses the ideaExpert measured, per direction
Owner, 2026-10-02. The trial is the **hypothesis measured**, not the idea: each idea file's «Hipótesis medidas» once
per study (its largest figure — addenda restate the total). **Long and short do not share**: the study's direction is
its template's `shape`; an idea with no template yet counts in every study of its asset × timeframe × direction, and a
study whose family is no template gets both. **The market profile's and sweep's measures stay out** of N (shown beside
it, distinct criteria, not rows: a rerun appends duplicates). `ledger.report` reads
`studies.research.memory.trials.spent` and passes K to `trials.accumulated(frame, extra)`; `trials.py` imports no
study. K raises N, never sigma; the window and `core.archive.manifest` still show searches only. **Cost today: nil**.

## Evidence
`python3 -m ledger.report --study XAUUSD_H4_freeShellLong` (2026-10-02): N 15,967 → 15,996, benchmark
0.083981 → 0.083990; best candidate (Sharpe 0.0608, 1,300 days) DSR 0.20209 → 0.20199. `…freeShellShort`: N 14,483 →
14,512, benchmark 0.091110 → 0.091122, DSR 0.09146 → 0.09140. Had the profile entered (+441 per direction):
0.084118. `tests/test_ledger_ideas.py`: K = 0 identical, K = 29 over N = 50 → DSR 0.4025 → 0.3764.
`AlgoData/ideas/XAUUSD/2026-10-01-impulso-h4.md` says 24 in §3 and 29 in its addendum; the first-match regex read 24.
