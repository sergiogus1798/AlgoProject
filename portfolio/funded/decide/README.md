# portfolio/funded/decide — which account to buy, in one sentence, from the bank tables

Encargo 33 deliverable 4 (§3.5, §4). The search itself — plans × add-ons × risk × re-buy policy,
every configuration a ledger trial — runs in `portfolio/funded/sim/`; this folder reads the tables
it wrote and says what to buy, **with the cost next to the gain**, or «ninguno: el valor esperado
no supera al mono». It simulates nothing and writes no ledger row.

```
AlgoData/portfolio/bank/<stamp>_<label>/ ─▶ tables ─▶ choose ─▶ run ─▶ bank/decisions/<stamp>.json
   table.parquet + manifest.json            per plan   gates     the sentence, in Spanish
```

**Imports from:** `portfolio.funded.sim` (`inputs`, the committed knobs), `core.datapaths`, pandas
**Consumed by:** `portfolio.funded.deals.worth` (`tables`), the window's funding view (the decision file)

| file | what it does | run it | in → out |
|---|---|---|---|
| `choose.py` | Encargo 33 §3.5 as a rule: which rows of the bank tables may be bought, why the others may not, and the one chosen. | imported | rows, owner → decision |
| `run.py` | THE COMMAND: which challenge to buy — the bank tables read by encargo 33 §3.5, the decision in Spanish with its cost beside its gain. | `python3 -m portfolio.funded.decide.run [--bank <folder> …] [--ignore-verdict]` | bank tables → stdout, `AlgoData/portfolio/bank/decisions/<stamp>.json` |
| `tables.py` | The bank tables on disk: every run of `funded.sim.run`, and per plan the latest one — its own portfolio's first. | imported | bank folders → plan → rows |

## What it does not decide (listed in every output, never defaulted)

The horizon of the bank simulation, which OOS segments set the edge level, how much a rank may move
across `h` before the choice is called fragile, whether the bar is the point EV or its interval's
lower bound, and the unseen data that validates the chosen combination (`DECISIONS.md` #11).

A plan whose table was drawn from another plan's portfolio is shown and never eligible: one
portfolio per plan (`PLAN.md` §14). `--ignore-verdict` exists to exercise the code on the test
root, where no verdict passes; its output is marked AJUSTADO and is not a decision.
