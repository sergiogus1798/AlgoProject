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
| `tables.py` | The bank runs on disk, newest first, synthetic ones left out; per plan, the table to use: the one of the plan's **own** portfolio (`manifest.paths.source.plan`) beats a newer one drawn from another plan's | imported | bank folders → plan → rows |
| `choose.py` | `GATES`, in order: own portfolio → verdict favourable → OOS edge > 0 → cash outlay p90 within the budget → EV(h decides) > 0 → EV above the monkey. The choice is the highest EV among the rows that pass all; `tie` when the runner-up is inside 2 standard errors; `ranks` gives each row's rank at every `h` | imported | rows, owner → decision |
| `run.py` | **THE COMMAND**. Refuses when the tables were made under different owner inputs or gaps, or under knobs that are not the committed ones; prints AJUSTADO when the verdict was ignored or the source run was relaxed; lists the readings it did not choose (`OPEN`) | `python3 -m portfolio.funded.decide.run [--bank <folder> …] [--ignore-verdict]` | bank tables → stdout, `AlgoData/portfolio/bank/decisions/<stamp>.json` |

## What it does not decide (listed in every output, never defaulted)

The horizon of the bank simulation, which OOS segments set the edge level, how much a rank may move
across `h` before the choice is called fragile, whether the bar is the point EV or its interval's
lower bound, and the unseen data that validates the chosen combination (`DECISIONS.md` #11).

A plan whose table was drawn from another plan's portfolio is shown and never eligible: one
portfolio per plan (`PLAN.md` §14). `--ignore-verdict` exists to exercise the code on the test
root, where no verdict passes; its output is marked AJUSTADO and is not a decision.
