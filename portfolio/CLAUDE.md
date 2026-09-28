# portfolio — combining strategies

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

**Where a strategy comes from: the archive.** A strategy enters from `AlgoData/archive/<identity>/<version>/`
(`core/archive/`, encargo 23), frozen with its `.sqx`, its cosecha rows, every study result, the
asset card of that day and the ledger count (N strategies tried) that deflates its Sharpe. The
window's PORTFOLIOS zone lists it and «Importar» shows it as the Estrategia page, read from the
archive with nothing recomputed (`ui/desktop/portfolios/`). Importing from a live databank waits
for the owner. The portfolio maths itself is not built yet.

A funded account's rules (daily loss cap, total drawdown, minimum days) are constraints on the
portfolio, not filters applied afterwards. When that work starts, they get written down here first.
