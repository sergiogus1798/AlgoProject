# portfolio/funded/rules — a prop firm's challenge as a machine over daily equity

Encargo 33 deliverable 2, milestone F1 of `portfolio/PLAN.md` §14.5. Pure functions: a plan's rules
read from the catalogue (`AlgoData/funding/funding.sqlite`, read-only), and a machine that walks a
path of server days — closed P&L, floating at the day's end, the day's worst and best equity — and
says whether the challenge passes, fails (and on which rule) or is still open. The engine calls it
to choose a funded portfolio; the bank simulation (F5) will call it too.

**Imports from:** `core.datapaths`, numpy, numba · **Consumed by:** the engine's funded objective (F2), `funded/sim/` (F5)

| file | what it does | run it | in → out |
|---|---|---|---|
| `catalog.py` | One plan's stages and rules, normalised, with every unconfirmed or conflicting rule it used named in `flags` | imported | plan key → dict |
| `floors.py` | One function per rule: the daily floor, the max-loss floor, the target, minimum days, consistency | imported | state → number, bool |
| `machine.py` | The challenge from one start day (reference) and from many start days at once (numba, identical), with an optional horizon: not passed by start + horizon − 1 reads «open» | imported | day arrays, plan, risk → outcome |

## Semantics (owner, 2026-09-30 — `PLAN.md` §12 «Answered»)
- **Breach is strictly below a floor**, checked on the day's worst equity (floating included).
- **Hantec trailing** rises with the intraday equity high, before the day's low is checked; **FTMO
  1-step** trails the highest end-of-day balance. Both unconfirmed, flagged.
- **A target is met on the closed balance at the day's end**; a day's profit is its closed P&L.
- **An unconfirmed rule is used as the catalogue reads it and flagged**, never silently trusted.
- Weekend and news bans are not checked here: they drop a strategy from a plan's pool before the
  search (owner, encargo 33 §6.2).
