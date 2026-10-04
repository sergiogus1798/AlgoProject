# construct/search — which combinations are allowed, and (later) which one is chosen

Reads the build slice only: `run.py` will hand it `matrix.segment(…, "build")` and nothing else
(PLAN §5.3, test §8.4). It holds the admissible graph (M2) and the funded search's stage A (F2): P(pass) of one plan
within 126 trading days, from every build start day, over the risk grid, for whole generations of
combinations at once on every core. The search by ranks (M3, 2026-10-04) sits beside it: the
mean signed rank of four path metrics on build, every clique when they are few, the GA otherwise.

**Imports from:** `pairs/`, `portfolio.funded.rules`, `ledger`, and `verdict/metrics` (pure path
metrics; the reverse import stays forbidden) · **Consumed by:** `../funded.py`, `../real.py`, the Parejas tab

| file | what it does | run it | in → out |
|---|---|---|---|
| `stagea_data.py` | One firm clock's build days as dense member × day arrays (closed, floating at the end, opened) and build-only M5 blocks, each member scaled to fixed risk by its factor | imported | universe → arrays |
| `stagea.py` | P(pass within the horizon) of every combination of a batch at every risk level: joint days and joint intraday low/high, the rule machine's kernel, numba `prange` over combinations; NaN where a lot would round to zero | imported | arrays, batch, plan → [M, L] |
| `greedy.py` | Starting sets: shuffled greedy maximal cliques of the admissible graph | imported | graph → cliques |
| `genetic.py` | The GA as functions: tournament, union crossover, add/remove/swap mutation, children repaired to cliques (least-connected member dropped), elitism, stop on stagnation of the absolute best; hands the whole generation to the objective at once | imported | graph, score → every evaluation |
| `trials.py` | The funded path's ledger rows, each in `PORTFOLIO_<pool>_construct` and in every member's study: stage A's search (every evaluated P(pass) as scores), stage B's (shortlist × risk settings) and the verdict's look per segment; `admit` asks the door first | imported | run → rows |
| `shortlist.py` | A search's distinct combinations best first, and the diverse cut: none sharing more than half its members with one already kept (half of the smaller or the larger — a required knob) | imported | search frame → shortlist |
| `stageb_data.py` | What stage B reads per member on one stretch: day figures, the exact minute arrays on one UTC grid (workers write them to shared memory, never return them), the trade units; a combination's joint server days with the exact M1 low and high | imported | sources, bars, day table → arrays |
| `stageb.py` | One combination under D, T1 and T2 at every block length (Politis-White plus the sweep) and every risk per phase; the setting kept is the best of the most pessimistic figures; the stability check | imported | data, combination, plan → rows, decision |
| `stageb_run.py` | Stage B over a whole shortlist and its winner; the same measures re-read on another stretch at the chosen risk (real path from every start day, and the Monte Carlos) | imported | shortlist, data → rows, table, winner |
| `stageb_null.py` | The selected null's searches: random admissible combinations sized like the real search's, scored and shortlisted the same way | imported | graph, score → shortlist |
| `objective.py` | M3's build score (Q10 a): each equal-weighted combination's RAR, R-cubed, gain-to-pain and P(losing year), and the mean of their signed ranks inside a reference set fixed for the run | imported | member paths, membership → metrics, score 0..1 |
| `exhaustive.py` | Every clique of every size, or None above `real.exhaustive_max` | imported | graph → membership |
| `choose.py` | M3's search: exhaustive with the ranks taken in the whole space, else the GA with the ranks taken in the greedy seeds (`real.rank_reference`, required) | imported | member paths, graph → every evaluation, the best |
| `admission.py` | Q16 (c): a candidate against a fixed base — the base members it has no admissible pair with, and its increment to the build Sharpe, `finite` or `marginal` | imported | member paths, graph, base → one row per candidate |
| `trials_real.py` | M3's ledger rows at step 27 on build: every evaluated combination's daily Sharpe in `PORTFOLIO_<pool>_construct` (the spread the oos2 deflated Sharpe will read), the count alone in each member's study; an admission pass | imported | search result → rows |
| `admissible.py` | The graph of pairs that clear every threshold (|ρ| two-sided, tail and co-loss one-sided, rolling only with ≥ 60 shared months), why each pair fails, the relaxed flag, effective N calm and stressed | imported | pairs frame → graph, failures |

## Traps
- **The rank score is only comparable inside one run**: it is a rank in that run's reference set.
  Across runs compare the four metrics, which `search.parquet` keeps.
- **A path with no drawdown reads NaN** in R-cubed and gain-to-pain (a mean of nothing) and ranks
  as the best; ten years of a real portfolio always has one.
- **A member's days before its history count as 0** in a combination's path (`real.py`).
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
