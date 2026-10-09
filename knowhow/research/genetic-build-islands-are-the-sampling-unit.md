---
q: Are the strategies of one SQX genetic build independent draws when I compare two builds or count survivors?
kw: batches lotes efecto de lote overdispersion phi 38 islands islas Strategy island.generation.n binomial chi-square homogeneity false alarm survivors clustered one island 19 of 56 relatives parientes permutation relabel islands trocear RAM 100k in 10k batches
tag: 🔬  date: 2026-10-07  see: research-lessons
---
# The island, not the strategy, is the unit chance acts on in a genetic build
SQX names a genetic build's strategy `Strategy <island>.<generation>.<n>`, and an island evolves
relatives: counts by gate destination spread across the islands of ONE build φ ≈ 38 times a
binomial's variance, and 19 of 56 step-8 survivors came from one island of 20. So compare builds
by relabelling whole islands (`studies/screening/batches`), never by a binomial on strategies; a
build's N survivors are at most as many bets as the islands that gave them; and a rule's kill
count varies between builds about √φ ≈ 6 times its binomial error.

## Evidence
🔬 2026-10-07, `Test_USDJPY_M30_doubleROCLong_10k`, gate `verdict.csv`: islands 1..20, generations
1..25 read from the names; `project.cfx` carries `<Islands>20`, `<MaxGenerations>25`,
`<PopulationSize>250`, `generationType="genetic-evolution"`. Survivors per island: 0 5 4 2 1 0 6 5 0
0 0 19 3 4 1 1 0 0 5 0. Splitting the same build's islands into even/odd halves gives a
between-halves chi-square of 484 on 6 df (binomial p ≈ 0) and a permutation p of 0.24 over islands.
🔬 2026-10-08, five builds of that cell (lot 1 + `_B2`..`_B5`, 50,000 strategies, same setup): step-8
survivors per build 56, 48, 10, 31, 72 — 13 times a Poisson's variance between builds, 6.5 times
between the 100 islands; 45 islands gave none and five gave 75 of the 217. Island-permutation p of
the five funnels 0.018, of alive/dead alone 0.057; no identity repeated. The islands are not the
floor either: daily-PnL correlation of the 217 survivors gives 21 groups at r > 0.7 (one of 146) and
5.5 effective bets by eigenvalue participation, and that number stopped growing with builds (4.5,
4.9, 5.5, 5.7, 5.5 after one to five). Survival falls with the generation a strategy was born in:
0.71 % under generation 10, 0.50 % for 10-19, 0.26 % from 20 on. All 217 survive in limbo.
