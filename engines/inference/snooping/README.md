# snooping — which strategies beat their benchmark once the whole search is paid for

Encargo 10's engine. Computes, never judges: it takes a panel of daily excess returns — each
strategy's profit minus whatever its benchmark earned that day — and says whether any column
beats zero (Hansen's SPA) and which ones can be named (Romano and Wolf's StepM). What the
benchmark is, and what a named strategy means, is the study's business
(`studies/screening/snoopingScreen/`).

| file | what it does | run it | in → out |
|---|---|---|---|
| `superior.py` | The stationary bootstrap's block length (Politis–White), the SPA's three p-values, and the StepM set | imported | T×K excess panel → p-values, names |

## What it does not answer, and how that differs from the CSCV

The CSCV (step 18) asks whether *the way parameters are chosen* overfits, over the variants of
**one** mother. This asks which of **K strategies** beat their benchmark with the search over those
K discounted. Different matrix, different question; they are not substitutes.

**It only corrects for the K it sees.** Strategies tried and discarded before the panel was built
are invisible to the bootstrap. That count is the ledger's (`ledger/`), and a caller that hands in
a pre-filtered panel is testing a smaller search than the one that was run.

## Two conventions worth knowing

- **Losses in, profits out.** `arch` ranks by loss, lower better. The panel goes in negated against
  a zero benchmark, so what the test compares is exactly the excess column, whatever the caller
  subtracted to build it — a benchmark can be different for every column.
- **One block length for the whole panel**, the median of each column's own: the bootstrap draws
  whole days across every column at once, which is what carries the correlation between
  strategies into the null.

A column that never moves (a strategy with no position in the window) has no variance to
studentize by; the caller keeps it out, and it could not have been named anyway.
