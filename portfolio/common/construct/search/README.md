# construct/search — which combinations are allowed, and (later) which one is chosen

Reads the build slice only: `run.py` will hand it `matrix.segment(…, "build")` and nothing else
(PLAN §5.3, test §8.4). It holds the admissible graph (M2) and the funded search's stage A (F2): P(pass) of one plan
within 126 trading days, from every build start day, over the risk grid, for whole generations of
combinations at once on every core. The search by ranks (M3, 2026-10-04) sits beside it: the
mean signed rank of four path metrics on build, every clique when they are few, the GA otherwise.

**Imports from:** `pairs/`, `weights/`, `portfolio.funded.rules`, `ledger`, and `verdict/metrics` (pure path
metrics; the reverse import stays forbidden) · **Consumed by:** `../funded.py`, `../real.py`, the Parejas tab

| file | what it does | run it | in → out |
|---|---|---|---|
| `admissible.py` | The admissible graph: which pairs of a pool clear every pairwise filter. | imported | pairs frame → graph, failures |
| `admission.py` | Admission to a base (Q16 c): pair filters against each member and Sharpe, one entry at a time. | imported | member paths, graph, base → one row per judgement, round by round |
| `choose.py` | The search by ranks (M3): every admissible combination when they are few, the GA otherwise. | imported | member paths, graph → every evaluation, the best |
| `exhaustive.py` | Every admissible combination of a small pool: all cliques of the graph, up to a limit. | imported | graph → membership |
| `genetic.py` | AlphaForge's genetic search over admissible cliques, rewritten as plain functions on numpy masks. | imported | graph, score → every evaluation |
| `greedy.py` | Shuffled greedy maximal cliques: the genetic algorithm's seed population (AF genetic.py:416-554). | imported | graph → cliques |
| `objective.py` | The build score of a combination (Q10 a): signed ranks of four path metrics, shifted minimum. | imported | member paths, membership → one metrics table per shift, score 0..1 |
| `random_k.py` | The real path's null (Q11 d; owner 2026-10-05, R6): random admissible combinations of one size. | imported | graph, K → membership, index, n_space |
| `shortlist.py` | The diverse shortlist: the best combinations of a search, no two sharing more than a set share of members. | imported | search frame → shortlist |
| `stagea.py` | The funded search's stage A objective: P(pass) of a plan per combination, over a risk grid. | imported | arrays, batch, plan → [M, L] |
| `stagea_data.py` | Per-member build-day and M5 block arrays for one firm, scaled to per-(risk x size) units. | imported | universe → arrays |
| `stageb.py` | Stage B of the funded search: one combination under three Monte Carlos, every block length, every risk. | imported | data, combination, plan → rows, decision |
| `stageb_data.py` | What stage B reads per member on one stretch of server days: day figures, exact minutes, trade units. | imported | sources, bars, day table → arrays |
| `stageb_null.py` | The selected null's searches: random admissible combinations put through the same selection. | imported | graph, score → shortlist |
| `stageb_run.py` | Stage B over a whole shortlist, its winner, and the same measures re-read on another stretch. | imported | shortlist, data → rows, table, winner |
| `trials.py` | The funded path's ledger rows: the pool's own study, and one row in every member's own study. | imported | run → rows |
| `trials_real.py` | The rank search's ledger rows (PLAN §6): the pool's own study and one row in each member's. | imported | search result → rows |

## Traps
- **The rank score is only comparable inside one run**: it is a rank in that run's reference set.
  Across runs compare the four metrics, which `search.parquet` keeps.
- **A path with no drawdown reads NaN** in R-cubed and gain-to-pain (a mean of nothing) and ranks
  as the best; ten years of a real portfolio always has one.
- **A member's days before its history count as 0** in a combination's path (`real.py`).
- **RAR can never prefer a combination to its best member**: a regression slope is linear, so an
  equal-weighted combination's RAR is the mean of its members'. A combination wins only through
  R-cubed, gain-to-pain and P(losing year); a pool of near-clones is answered with K = 1
  (`knowhow/research/rank-score-rar-is-a-mean.md`).
- **The GA's rank score saturates** 🔬 2026-10-05 (`tests/portfolio_planted.py`'s pool forced to the GA
  with `real.exhaustive_max=20`, default GA knobs, 3 seeds): the reference is the greedy seeds, which
  are MAXIMAL cliques (K 4-6, diluted), so any combination better than all of them scores 1.0 and the
  search stops on stagnation after 12 generations having scored K ≤ 2 three times in 3,600. It
  returned {A, B, N0, N1, N3}; the exhaustive search of the same 159 combinations returns {A, B}.
  Only pools above `real.exhaustive_max` reach the GA: 1,000,000 combinations since 2026-10-05
  (owner; was 100,000; ~11 min on one core at the limit, OPEN #104). Above it the GA still runs
  and its rank score still saturates — open, the owner's (PLAN §12, reading 9).
- **The table a run stores is the one its score stands on**: the four metrics of `search.parquet`
  are each the worst of the shifted windows. The Sharpe is always the whole window's (the ledger's spread).
- **Admitting against a fixed base lets two clones of one idea both in** — each helps alone. `sequence`
  is what the command runs; `judge` alone is one round.
- **Throughput** 🔬 2026-09-30, synthetic 50-member pool, 10-year build: ~1,500-1,860 combinations/s
  on 48 cores (165/s on one), 1.3 GB — measured while the custodian ran a job; a GA of 30,000
  evaluations is ~20 s per plan.
- **A child that is not a clique is repaired structurally**, not by score (PLAN §5.3 left it open;
  scoring each repair would cost a batch call per child).
- **Duplicated combinations are scored and counted again** in the ledger's `n_scored` — N is
  overstated, never understated.
- **Under 24 shared months a pair is rejected (`overlap`)**, whatever its coefficients (owner, Q8).
- **Independent strategies fail these filters too**: 75 % of independent pairs pass on a 10-year
  build, so a K-member clique of independents is rare (`knowhow/research/pair-filters-false-rejection.md`).
