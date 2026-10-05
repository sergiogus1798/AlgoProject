# portfolio — combining strategies

**The implementation plan is `PLAN.md`** (2026-09-30): module layout, data shapes, every knob, the
AlphaForge port, tests, milestones and the owner's open questions (§12). **Order: M0-M2 (shared
universe and pairs) → F1-F5 (the funded path, §14 — the owner's priority) → M3-M8 (the real-account
path) → M9 (paper OOS).** A milestone blocked by an open question does not start on a guessed default.

**Before building anything here, read `BUILD_COMPENDIUM.md` end to end** (owner, 2026-09-28). It
holds every practice, test and trap gathered for this module: what to port from the owner's
AlphaForge repo and what to redo, and every portfolio idea of the books-and-internet dossier
(`docs/AgentPDFs/ideas-de-internet-y-libros-2026-09-27.md` §5). None of it is accepted yet; its
§13 lists what the owner must decide first.

Two destinations with different constraints: `funded/` for prop-firm accounts, `real/` for the
owner's own capital. `common/` holds what both need.

The design is not settled. `DECISIONS.md` is where the open questions live; add to it rather than
inventing an answer. What is agreed so far:

- Correlation is measured between **equity curves**, not between metrics.
- A portfolio's drawdown is computed on the aggregated curve, never summed from the parts.

**Settled decisions** (owner, 2026-09-29 and 2026-09-30) are no longer listed here: the 2026-09-29 ones
(engine first, sizing to encargo 33, every threshold 0.30, no same-asset filter, pluggable weights,
`build` → `oos1`+`oos2`, same pool, siblings, development reads the archive, only validated strategies,
the funded rules split) are in `DECISIONS.md` «Settled by the owner»; the 2026-09-30 ones (Q1-Q17, fixed
risk, funded rules) in `PLAN.md` §12 «Answered» and §14; the compute rule (all physical cores, under 80 GB,
built for speed first) in `EXECUTION.md` (compute rule); the 2026-10-04 ones, taken by the Council on
the owner's delegation (Q10, Q11, Q16 provisional, #2, #5, #12, live incubation after `oos2`), in
`PLAN.md` §12 and `DECISIONS.md`, with the readings they leave open; the owner's 2026-10-05 answers
to those readings (R1-R7, admission in sequence, the funded verdict's measure) in `DECISIONS.md` «Settled by the owner — 2026-10-05».
Status per milestone: `PLAN.md` §9.

**Where a strategy comes from: the archive.** A strategy enters from `AlgoData/archive/<identity>/<version>/`
(`core/archive/`, encargo 23), frozen with its `.sqx`, its cosecha rows, every study result, the
asset card of that day and the ledger count (N strategies tried) that deflates its Sharpe. The
window's PORTFOLIOS zone lists it and «Importar» shows it as the Estrategia page, read from the
archive with nothing recomputed (`ui/desktop/portfolios/`). Importing from a live databank waits
for the owner. The portfolio maths is built (2026-10-05) in `common/construct/` and `funded/`, tested only on the relaxed Nikkei test pool in the test root — no real result yet (PLAN §9).
**What each firm sells and under which rules is already a database**: `funded/catalog/`
(`AlgoData/funding/funding.sqlite`, Hantec and FTMO, every add-on combination priced), refreshed
every Sunday by the `fundingWatcher` agent. The economics on top of it is encargo 33.

**Testing this module never writes the real root.** A test run is the real code under
`ALGO_DATA_ROOT=<AlgoData>/portfolio/_test/root` (`portfolio/testroot/README.md`): its own ledger,
archive, pools and runs, the pool `Test_nikkei_ref`, relaxed thresholds passed with `--set`. Every
such process prints «RAÍZ DE PRUEBA» and none of its numbers is a result.
