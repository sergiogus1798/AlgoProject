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

**Only validated strategies enter** (owner, 2026-09-29): a strategy that passed steps 1-25 and
whose MT5 backtest on a prop firm's feed matched SQX's (step 26, encargo 34) joins that firm's
**validated pool**, and the portfolio reads only from it. `oos2` is spent by then.

**Where a strategy comes from: the archive.** A strategy enters from `AlgoData/archive/<identity>/<version>/`
(`core/archive/`, encargo 23), frozen with its `.sqx`, its cosecha rows, every study result, the
asset card of that day and the ledger count (N strategies tried) that deflates its Sharpe. The
window's PORTFOLIOS zone lists it and «Importar» shows it as the Estrategia page, read from the
archive with nothing recomputed (`ui/desktop/portfolios/`). Importing from a live databank waits
for the owner. The portfolio maths itself is not built yet.

A funded account's rules (daily loss cap, total drawdown, minimum days) are constraints on the
portfolio, not filters applied afterwards. When that work starts, they get written down here first.
**What each firm sells and under which rules is already a database**: `funded/catalog/`
(`AlgoData/funding/funding.sqlite`, Hantec and FTMO, every add-on combination priced), refreshed
every Sunday by the `fundingWatcher` agent. The economics on top of it is encargo 33.
