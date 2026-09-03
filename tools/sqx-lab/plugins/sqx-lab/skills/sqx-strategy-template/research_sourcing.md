# Autonomous research sourcing — find edges, falsify them, bind them to THIS install

> Optional autonomous front-end to **SKILL.md Step 1**. When the user says *"propose options"*,
> *"find me edges from the literature"*, or *"what's worth building"* (instead of handing over a
> concrete idea), follow this contract to produce **candidate theses already bound to catalog groups
> and an existing shape**. Those candidates feed `research_agent.md` (Step 2). This layer produces
> **theses, never final `.sqx`** — it front-loads the design agent, it does not replace it, and it
> never bypasses install-only resolution or the AlgoWizard build-confirm gate.
>
> Claude has **WebSearch / WebFetch**. Use them. This is **structural sophistication sourcing, not a
> profitability promise** — nothing here claims an edge makes money.

## What this layer is for

Turn the open literature into a *short* list of mechanism-backed edge hypotheses that **this install
can actually express** and that survive a pessimistic falsification pass — then hand them to the
design agent as ready-to-finish specs.

## Step A — Frame against the install (read `catalog.json` first)

List what this install can express, by role:
- **Filters (regime/context):** `FilterTrendDirection`, `FilterRegimeTrending`, `FilterVolExpansion`, `FilterSession`
- **Triggers (events):** `EntriesBreakout`, `EntriesTrend`, `EntriesMeanRevert`, `EntriesMomentum`
- **Price pools (levels):** `LevelsTrailingStop`, `LevelsVolBands`, `LevelsPriorPeriod`, `LevelsTargets`

Phrase the search as: *"edges expressible as a **filter (regime/context) AND a trigger (event)**,
optionally executed against a **price level**, optionally with a **higher-timeframe** regime gate."*
Do **not** search open-endedly for "profitable strategies" — search for **mechanisms** the catalog
can host.

## Step B — Source candidates (WebSearch + WebFetch)

Run **3–6** searches over durable, mechanism-backed families: factor/anomaly literature (time-series &
cross-sectional momentum, volatility/regime conditioning, breakout & range-expansion, mean-reversion,
session/intraday seasonality, multi-timeframe trend alignment), quant blogs, and survey papers. Prefer
sources that state a **mechanism** and report **robustness / out-of-sample** — not a single-market blog
backtest.

For each promising hit, `WebFetch` and extract a **candidate card**:
- edge in one sentence · proposed **mechanism (why it persists)** · the **conditioning variable** (the
  filter) · the **trigger event** · the strongest **caveat**.

Pull **5–8 raw candidates** so the gate has material to cut.

## Step C — Capture citations verbatim

For every candidate, record: **title · author/venue · year · URL · one quoted sentence** that states
the edge or its mechanism. No traceable, mechanism-bearing source → the candidate is dropped at the
gate (check 6). Paraphrase-only claims do not count.

## Step D — FALSIFICATION gate (pessimistic; default = REJECT)

A candidate survives **only if it passes all six**. Record the first failing check for every reject.
**Do not soften a hypothesis to make it pass** — drop it.

1. **Look-ahead / repaint** — computable at bar close with correct shift (OHLC shift ≥1, channel/level
   shift ≥2, no forming bar, no repainting indicator). Uses the future → REJECT.
2. **Regime-fragility** — the source gives a reason it persists across regimes, *or* names the regime it
   needs (which becomes the filter). "Worked 2010–15 on EURUSD", no mechanism → REJECT.
3. **Overfit / DOF** — expressible with few free params: ~one filter + one trigger + at most one price
   pool, exits left to the proven stack. Needs many bespoke thresholds / a magic lookback / per-symbol
   tuning to exist → REJECT.
4. **Install-expressibility** — conditioning variable **and** trigger each map to a catalog Condition
   group, any level to a catalog Value group, correct type. No catalog group can carry it → REJECT (or
   **DEFER**, see mapping rule).
5. **Mirror-asymmetry** — has a coherent **short mirror** (`NegatedCondition`/`OppositeValue`), since
   skeletons mirror long→short. Inherently long-only (e.g. index drift) → REJECT *unless* an explicit
   long-only shape (`stop_long_single` / `two_entry_market` / `multi_leg`) is chosen.
6. **Citation integrity** — a traceable source with a stated mechanism exists (Step C). "It just works"
   / marketing / un-sourced paraphrase → REJECT.

> Passing the gate is **not** a profitability claim. It certifies the hypothesis is structurally sound,
> install-expressible, mirror-able, and worth turning into a **build-confirmable** template.

## Step E — INSTALL-MAPPING (survivor → bound design spec)

Bind each survivor to **names that already exist in `catalog.json`**:

| Edge ingredient | Bind to (catalog) |
|---|---|
| trend regime (direction) | `FilterTrendDirection` |
| trend regime (strength) | `FilterRegimeTrending` |
| volatility regime | `FilterVolExpansion` |
| time-of-day / seasonality | `FilterSession` |
| breakout / range-expansion event | `EntriesBreakout` |
| trend-cross event | `EntriesTrend` |
| oscillator snap-back | `EntriesMeanRevert` |
| momentum thrust | `EntriesMomentum` |
| trailing / structural stop | `LevelsTrailingStop` |
| volatility band | `LevelsVolBands` |
| prior-period structure (prev-day/week high) | `LevelsPriorPeriod` |
| profit target | `LevelsTargets` |

Rules: **filter ≠ trigger** (never two of a kind); a price pool only if the edge executes against a
level, and on the **trade side** (Levels groups are long/upper-side; the skeleton mirrors for shorts).
Pick a **shape** that matches the mechanism: confirmation-on-breakout → `stop`; **higher-timeframe
regime gate → `mtf_filter`** (the filter evaluates on the daily chart); regime+trigger already the edge
→ `market`; one dominant regime/trigger → `market_single`; intraday/seasonal → `session_market`;
*regime AND trigger AND NOT veto* (exclude a spoiling context) → `role_market`; several independent
setups → `multi_leg`.

**THE HARD RULE — never invent.** If the edge needs a conditioning variable, trigger, or level that
**no catalog group provides**, you have exactly two legal moves:
- **DEFER** — invoke `sqx-random-group` to author the missing pool from the install's own blocks,
  build/validate it, refresh `catalog.json`, then return and bind; **or**
- **DROP** — record why and move to the next candidate.

Emit each survivor in the `research_agent.md` spec schema, carrying the falsifiable thesis **and** the
citation:

```json
{ "name": "TrendFilteredBreakout", "shape": "stop",
  "filter": "FilterTrendDirection", "trigger": "EntriesBreakout", "price_pool": "LevelsPriorPeriod",
  "roles": { "FilterTrendDirection": "regime filter", "EntriesBreakout": "breakout trigger",
             "LevelsPriorPeriod": "stop level" },
  "thesis": "Breakouts taken only in the trend regime follow through more than counter-trend ones.",
  "source": "Author/Venue, Year — URL" }
```

## Step F — Hand off to the design layer

Pass the bound specs into **SKILL.md Step 2** (`research_agent.md`). The design agent maps each to an
**archetype**, confirms roles, enforces **confluence-not-redundancy**, finalizes the shape;
`generate.py` (Step 3) transplants into a build-confirmed skeleton and self-validates; the user
**imports + Builds** (Step 5) — the sole oracle of validity (**THE VALIDITY GAP**). This protocol feeds
that flow; it never short-circuits it.

## Guardrails (load-bearing)

- **Install-only** — never invent a block/group; bind to `catalog.json` or DEFER/DROP.
- **No profitability claims** — structural sophistication, not PnL. Citations describe a *hypothesis*.
- **Doesn't bypass the pipeline** — outputs theses → specs only; `generate.py` self-validates and an
  AlgoWizard Build remains the only proof.
- **Only advertised shapes** — `stop`/`market`/`market_single`/`session_market`/`role_market`/
  `mtf_filter`/`stop_long_single`/`two_entry_market`/`multi_leg`. Novel structure goes through the
  lab→product loop, not this protocol.
- **Pessimistic + auditable** — default REJECT; record the failing check for every cut.
- **Mirror + hygiene preserved** — coherent short mirror (or explicit long-only shape), low DOF,
  correct shift discipline → survivors stay inside proven skeleton territory.
- **Filter ≠ trigger** — never two Condition groups of the same kind; confluence-not-redundancy is
  enforced at mapping time and re-checked by the design agent.
