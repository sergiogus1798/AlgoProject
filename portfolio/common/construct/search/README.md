# construct/search — which combinations are allowed, and (later) which one is chosen

Reads the build slice only: `run.py` will hand it `matrix.segment(…, "build")` and nothing else
(PLAN §5.3, test §8.4). It holds the admissible graph (M2) and the funded search's stage A (F2): P(pass) of one plan
within 126 trading days, from every build start day, over the risk grid, for whole generations of
combinations at once on every core. The real account's search (M3) waits on Q10, Q16, #2.

**Imports from:** `pairs/`, `portfolio.funded.rules`, `ledger` · **Consumed by:** `../funded.py`, the Parejas tab

| file | what it does | run it | in → out |
|---|---|---|---|
| `stagea_data.py` | One firm clock's build days as dense member × day arrays (closed, floating at the end, opened) and build-only M5 blocks, each member scaled to fixed risk by its factor | imported | universe → arrays |
| `stagea.py` | P(pass within the horizon) of every combination of a batch at every risk level: joint days and joint intraday low/high, the rule machine's kernel, numba `prange` over combinations; NaN where a lot would round to zero | imported | arrays, batch, plan → [M, L] |
| `greedy.py` | Starting sets: shuffled greedy maximal cliques of the admissible graph | imported | graph → cliques |
| `genetic.py` | The GA as functions: tournament, union crossover, add/remove/swap mutation, children repaired to cliques (least-connected member dropped), elitism, stop on stagnation of the absolute best; hands the whole generation to the objective at once | imported | graph, score → every evaluation |
| `trials.py` | The ledger rows: one in `PORTFOLIO_<pool>_construct` and one in each member's study, every evaluated P(pass) as scores | imported | run → rows |
| `admissible.py` | The graph of pairs that clear every threshold (|ρ| two-sided, tail and co-loss one-sided, rolling only with ≥ 60 shared months), why each pair fails, the relaxed flag, effective N calm and stressed | imported | pairs frame → graph, failures |

## Traps
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
