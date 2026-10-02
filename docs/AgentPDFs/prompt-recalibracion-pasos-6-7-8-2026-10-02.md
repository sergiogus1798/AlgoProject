# Prompt — redo the calibration of steps 6, 7 and 8, by asset × timeframe × strategy family

Outbound brief (owner, 2026-10-02): paste everything below the line into a fresh session. English
because an agent reads it; it reports to the owner in Spanish.

---

You are the lead of a team of agents. **Redo the calibration of the selection criteria of workflow
steps 6, 7 and 8** — the acceptance filters of the SQX Build on the in-sample (step 6) and the
Pass / Limbo / Fail rules of the Python analysis after the out-of-sample retest (steps 7-8) — on
correctly built populations, with a new dimension: **the strategy family**. Talk to the owner in
Spanish. Read `CLAUDE.md` first and obey every hard rule; rules 14 and 15 are new and are the
reason this study is being redone. Tokens are not a constraint: launch as many agents as the work
needs. Machine time is not either: 40 hours of builds is acceptable. Each single run must stay as
fast as it was (≈10 minutes per population).

## Why it is being redone

A first calibration ran on 2026-10-01/02 (`docs/AgentPDFs/criterios-pasos-6-y-8-2026-10-02.md` —
read it whole: reuse its method, its tooling and its conclusions, do not re-derive them). Its
populations were built wrong, so its step-6 numbers, its funnel and its A/B are not final:

1. **Too many conditions (rule 14).** The template used had two `RandomCondition` holes per side
   with «What to build» 1..2, so strategies carried up to 4 entry conditions (69 % had 3 or more).
   → `knowhow/authoring/condition-count-simple-vs-template.md`
2. **The whole palette (rule 15).** 842 blocks on, time/calendar blocks and stop/limit entry blocks
   included.
3. **Two assets only** (USDJPY, XAUUSD): every other asset's SQX session was missing.

What stays valid from it: the method, the unattended queue, the fast review path, the corrected
gate t, the null populations (11.9 M strategies, 17 assets) and the central step-8 line —
`gate.scorecard.drift_excess_t`, limbo ≥ 1.65 / pass ≥ 2.33 on H1 and M30 — which comes from the
nulls, not from the builds.

## The owner's instructions for this run

1. **His genetic options are the default for all SQX work in the project — already applied.**
   `sqx/projects/buildmode_model.xml` (copied verbatim into every project's Build) now carries the
   block he configured by hand in the GUI on 2026-10-02, with the population he then ordered:
   **PopulationSize 250 per island** · MaxGenerations 25 · CrossoverProbability 89 ·
   MutationProbability 20 · Islands 20 · MigrationModulo 10 · MigrationRate 3 ·
   FreshBloodWeakestPct 5 · FreshBloodWeakestGenerations 10 · no initial-population conditions ·
   restart on finish and on stagnation (5 generations) · fitness Ret/DD. He also set StrategyType
   `simple` and «What to build» entry 1..2 **and exit 1..2** (the doctrine had exit 0..2: make
   `assets/_build.yaml` / `buildrules.py` say what he set, and ask him if exit conditions are now
   mandatory everywhere). Still to do: a test that a new project's Build carries this block, the
   README of `sqx/projects`, the knowhow card and the manual chapter. Do not change these values.
2. **Condition count (rule 14).** At most 2 entry and 2 exit conditions. Without a fixed idea:
   **Simple Strategy**, 1..2 — no template is authored (the `freeShellLong` / `freeShellShort`
   templates are retired). With a template: 1 fixed + 1 `RandomCondition` → «What to build» 0..1
   on that side; 2 fixed → no hole. Fix the builder so it writes `2 − fixed` and refuses two holes
   on a side (`sqx/projects/buildrules.py` writes 2 whatever the template holds; OPEN.md #93), and
   verify on every population that no strategy exceeds the cap — count it, do not assume it.
3. **Palette (rule 15).** No block that reads the clock or the calendar (BarTime, CurrentTime, day
   of week / of month…) in any study or generation, now or later. No stop/limit entry blocks while
   orders are at market. **Never everything**: one run per strategy family, each with the
   conditions and indicators that suit it.
4. **The new dimension: strategy family.** A research agent is, right now, authoring one
   building-block palette per family (trend following, breakout, mean reversion…) and writing into
   each asset's card in `assets/symbols/` which families suit that asset and which do not. **Obey
   it**: do not test a family on an asset its card says it is bad for. Find that work before
   starting (`ListAgents`, the asset cards, `AlgoData/templates/`, the research director's files —
   `docs/AgentPDFs/director-de-investigacion-2026-10-01.md`, the `researchDirector` and
   `buildingBlocksExpert` agents); if it is not finished, coordinate with that session rather than
   inventing palettes or suitabilities of your own. If a card is silent on a family, ask the owner.
5. **Coverage:** at least 10-12 different assets, on **M30 and H1** (the timeframes he uses most).
   One direction per build (rule 13): long and short are separate populations.
6. **The criteria may vary** by asset, by timeframe and by strategy family. Say what must vary and
   what is safely global, with the evidence.
7. **Studies removed from this calibration — confirmed by the owner on 2026-10-02:** `feedQuality`
   (calidad del feed), `profitShape` (forma del beneficio) and `entryQuality` (calidad de la
   entrada). Do not run them, write no rule on them.
8. **What the criteria are for — the owner's own words, 2026-10-02:** «qué criterios he de poner,
   sobre todo en el IS de SQX, y en el primer cribado de OOS en la aplicación, para que (1) me
   salga un OOS robusto — esto depende mucho del IS — y (2) los tests del mono y demás cosas del
   paso 8 salgan aceptables». So the target is twofold and it is measured, not assumed:
   (1) which **in-sample** acceptance (step 6, in SQX) makes the **out-of-sample** robust — the
   emphasis is on the IS: find the IS quantities that predict a robust OOS, per asset, timeframe
   and family, and say plainly where none does; (2) which first OOS screen (steps 7-8) leaves
   strategies whose **step-8 tests come out acceptable** — the monkey (random-entry null), edge by
   cost, real-spread repricing, snooping, the gate's screens. The first calibration dropped the
   monkey's p as a rule because it is not reproducible (it seeds from OS entropy) and redundant
   with the t: here it is part of the **outcome**, so fix its seed first (a seed recorded per
   run) and report, for every candidate criterion, the share of survivors that pass the monkey at
   p ≤ 0.05 and the other step-8 tests, next to its cost in strategies.
   **The answer he wants for the IS is a concrete recipe**, in his words: «cuántos trades he de
   pedir (suelo de 35 por año), si he de pedir un PF mínimo, un KER, un Sharpe, o qué métricas he
   de usar». So, per asset × timeframe × family (pooled where the data allow): which IS metrics
   to filter on and at what value — trades per year (his working floor is now **35/yr**; test 20,
   25, 30, 35, 40, 50 and say what 35 costs and buys), profit factor, the Kaufman efficiency
   ratio, Sharpe, Ret/DD, SQN, stability, stagnation, win rate, average trade against cost, and
   any other column SQX can filter on (`knowhow/columns/`) — and which metrics NOT to use, with
   the evidence. A metric goes into the recipe only if SQX can express it as a Build condition on
   the in-sample; if the best predictor is not an SQX column, say so and give the closest one.
   Remember the finding to re-test: a filter inside the Build changed what the genetic search bred
   and lost good strategies, so each recommended filter is tried both inside the Build and as a
   cut afterwards, with replicas.
9. **Deliver** the criteria for the IS in SQX and for the OOS in the application, each threshold
   with its gain and its cost in strategies, in a Spanish dossier with its PDF, plus the rules
   written where they apply (`assets/_study.yaml`, `pipeline/autopilot/criteria.yaml`) marked as an
   agent's proposal.

## What the research session found — read before designing the cells

Added by the research-director session (`algoproject-de`, 2026-10-02) at the owner's request. It
corrects two pointers of instruction 4 and gives the findings that bear on this calibration. All of
it is uncommitted in the working tree.

**Where the family work actually lives (instruction 4 says "each asset's card" — it is not there).**

- **Suitability per asset: `assets/FAMILIAS.md`**, one document, not the cards in `assets/symbols/`
  (`core.assetwrite` has no such field). Regenerate with `python3 -m
  studies.research.marketProfile.report --familias`. Per asset and per timeframe (M15, M30, H1, H4)
  it lists the families in the order of the owner's qualitative prior
  (`AlgoData/research/literature/familias-por-activo-prior-2026-10-02.md`, which he trusts), each
  annotated with what was measured: «medido a favor» (26 entries), «sin evidencia medida» (93),
  «medido en contra» (7). A family the prior rates Baja is not listed. **The owner's rule is "use
  both": the prior decides what is worth trying, the statistics are a bonus** — so a listed family
  is allowed even without measured evidence, and «medido en contra» stays listed, flagged. Whether
  to spend builds on a «medido en contra» cell is a question for him, not a default.
- **Not covered by the prior:** USDCHF, UKOIL, USOIL (ranked from measurements only); CADJPY is
  treated as a yen cross. The prior's best mean-reversion markets (UK100, EURGBP, AUDNZD, EURCHF,
  NZDUSD) are not in `assets/`.
- **Palettes: `sqx/blocks/palettes/`** (not `AlgoData/templates/`): `ruptura_base_v2`,
  `reversion_base_v2`, `tendencia_base_v2`, `momentum_base`, `volatilidad_base`, `patron_base`,
  `sesion_base`. Guard: `tests/test_palettes_families.py` (no clock or calendar block, no
  stop/limit block, every key exists). **Not yet approved by the owner**: the three `_v2` sit next
  to the untouched originals (`ruptura_base`, `reversion_base`, `tendencia_base`, 148-180 blocks
  each, which do contain clock and stop/limit blocks). Ask him which set this calibration uses.
- **The palettes are deliberately tiny** — 6 to 13 blocks, "the blocks that ARE the family", one
  per kind of information. That is far under the 90-170 band the `buildingBlocksExpert` still
  asks for, and with Simple Strategy 1..2 the builder draws both conditions from the same handful.
  Open with the owner: is a family's palette the family alone, or the family plus the orthogonal
  kinds for the second condition (dossier `director-de-investigacion-2026-10-01.md` §5; draft
  table in `studies/research/board/palette.py`)? Applying several palettes to one project does not
  exist yet (`sqx/projects/buildingblocks.py` applies one).
- **`sesion` is out.** Its measures and the natural rules need the session clock; the owner
  rejects those blocks. `sesion_base` avoids `CurrentHour` but is built on `SessionHigh/Low/Open`,
  `HighD/LowD/OpenD` and the anchored VWAP, which depend on a time band — he has not said whether
  those count as reading the clock. Do not run a session family until he answers.
- **`patron` should not be a family run:** candle-pattern structure is real and pays 0.05-0.89×
  cost on all 19 assets, and the literature search found nothing usable. It is a weight-1 extra
  condition at most.
- **Pullback** is a family in the prior and not one of the seven keys; it has no palette. It is a
  trend context (higher-timeframe average) plus a reversion trigger.
- **Family keys.** Profile, memory and board use Spanish keys (`tendencia, ruptura, reversion,
  momentum, volatilidad, patron, sesion`); `sqx/blocks/taxonomy.yaml` uses English (`breakout,
  mean_reversion, trend, momentum, volatility, pattern, session`). The mapping is in
  `studies/research/board/`. For the family tag in project names, pick one set and say which.

**Traps found on the way that would silently spoil a population.**

- **A palette did not narrow anything between 2026-10-01 22:41 and the fix of 2026-10-02.** The
  taxonomy was fully labelled that evening (752 blocks got a neutral weight 1), and from then
  `palette.resolve` returned ~575 conditions for every curated palette, clock and stop/limit
  blocks included. Fixed: `unlabelled: off` plus a list is now exactly that list. After applying a
  palette, **count the blocks switched on in the project's Build** — do not assume.
  → `knowhow/authoring/builder-block-switches.md`
- **A value block with two roles cannot be switched for one role only**: on as an indicator means
  on as a stop/limit level too (`Close`, `SessionHigh`, `ATR`…). Rule 15's "no stop/limit entry
  blocks" therefore needs `buildingblocks.rewrite` never to switch on the `Stop/Limit…` keys; not
  done. `timeRangeBreakout` still carries four clock blocks and 20 dual-role values.
- **The taxonomy's seven weights were put by a rule script in one pass and are not reviewed** —
  a hint, not truth. `CBlock_BarsLargerRSI` and `_2` are all-zero (nobody knows what they compare)
  and so out of every palette. `CBlock_SqueezeOn`'s polarity is unverified.
- **Project prefix.** The owner wants the research director's projects named `Research_`; the
  builder still refuses it (patch pending on `sqx/projects/registry.py`, see
  `scratch/research-director/PENDING-research-prefix.patch.md`). This calibration's `Test_Calib_*`
  names are unaffected.

**What the market profile measured — priors for the cells, in-sample `build` only, never oos.**

`studies/research/marketProfile/` tests 99 naked rules (one condition, fixed parameters, mostly a
fixed-bar exit) per asset × timeframe × direction against a shuffled null: an event study in
Python, not SQX backtests. 14,364 tests; plus a sweep of 9 exits × 3 parameter steps (53,352
variants). Full account: `knowhow/research/market-profile-blind-spots.md`.

- **Cost is the wall at M15-H1, not the absence of structure.** Of the significant measures with
  trades, 155 of 158 at M15, 112 of 116 at M30 and 57 of 64 at H1 fail only on "mean effect ≥ 2×
  cost". Bar-to-bar reversion is significant in 87.5 % of cells and pays a median 0.2× cost.
  Expect a mean-reversion population at M30 to be large, significant-looking and unprofitable net:
  for that family the step-6 filter that matters is average trade against cost, not PF.
- **A better exit moves little:** the best of nine exits lifts the median effect from 0.08× to
  0.57× cost; what then pays is not significant. Do not expect the exit conditions (1..2) to
  rescue a family on an asset.
- **Where prior and measurement agree — the cells most likely to show enrichment:** breakout and
  momentum, **long**, on H1 (and M30) in DJ30 (the only cell that passes every filter naked:
  breakout with a D1 trend filter, 3.1× cost, 71 trades/yr), XAUUSD (momentum 3.9×, breakout
  3.7× at H1), GBPJPY, USDJPY, EURJPY. USDJPY long being the first calibration's only edge fits.
- **Single-asset trend following is absent at every horizon tried**, including lookbacks of
  100-200 bars and 20-252 days of D1 context: 0.8 % of 1,703 tests reach raw p ≤ 0.05. The prior
  rates trend Alta on gold and the yen crosses at H4; the variance ratio disagrees in 18 of 35
  comparable cells. A trend-family population there is the direct test — report it against its
  random twin whatever the outcome.
- **Dip-buying on indices is large in money and invisible in significance:** D1 RSI(2) < 10 above
  SMA200, long: USA500 13× cost (7× net of buy-and-hold), USATEC 17×, DJ30 12×, NIKKEI225 6×,
  DAX40 −4.7×. But 5-8 trades a year and raw p 0.07-0.17. Two consequences for this study: the
  35-40 trades/yr floor removes exactly the index reversion the literature documents — bring the
  owner that cost explicitly for index × reversion; and one asset over ten years cannot prove an
  effect of that size, so **pool by asset class** (the five indices together) where the family is
  the same.
- **Indices are asymmetric:** reversion measures are positive long and negative short at D1
  scale. A short reversion or short trend population on an index is expected to be chance; and a
  long one must be compared with buy-and-hold at the same exposure (the random twin does this —
  zero is the wrong benchmark there).
- **Six assets showed nothing naked** — AUDJPY, CADJPY, USA500 (bar H1 long reversion), XAGUSD,
  UKOIL, USOIL. On the oils the cost is 0.6-1.4× the ATR below H4 and the cost cards are still
  provisional.
- **Trade frequency by family is very uneven**, which is why thresholds will have to vary: the
  large naked effects sit at 3-25 trades a year (momentum on a 3-ATR bar at H4, D1-conditioned
  reversion), the frequent ones (67-91/yr) at 2-2.5× cost.
- **Literature** (62 sourced effects, `AlgoData/research/literature/edges-2026-10-02.{md,yaml}`,
  each with a `verified` flag): fast trend on indices and developed FX is reported as nearly gone
  since 2009; fast trend survives on metals and oils (5-20 days); what pays in index reversion is
  daily, long-only, conditioned on an uptrend; 21 of the 62 need the clock.
- **Swap.** The profile's cost leaves swap out; it changes no verdict today, but adds 57-83 % to
  the cost of multi-night FX holds at H4. Trap when computing it: forex swap points are in
  `tickStep = tick_size / 10`. → `knowhow/research/profile-cost-without-swap.md`

**Where to look.** The board the research director reads: `python3 -m studies.research.board`
(`AlgoData/research/board/board.txt`) — 359 cells today, too many to rank; the owner is deciding
whether to restrict it. Attempts and ideas already spent per cell:
`python3 -m studies.research.memory.report` (`AlgoData/research/memory/`). This calibration's
populations should end as rows there: `python3 -m studies.research.memory.report --close <run_dir>`
closes a finished autopilot run's row (`verdict.close_run`); the autopilot does not call it yet.

## First job — the sessions (solved, needs wiring)

Yesterday 122 of 160 populations failed with «ninguna tarea de este proyecto define la sesión
`<SYM>_ftmo`»: only `XAUUSD_ftmo` and `USDJPY_ftmo` are defined inside any `project.cfx`, and
`doctrine.borrow_session` looks nowhere else. **The sessions exist in SQX** (owner, 2026-10-02:
«usa las sesiones de FTMO, están en SQX»): the Data Manager keeps all of them in the install's
`user/data/data.db` (SQLite: `SESSIONS`, `ELEMENTS`) — 102 FTMO sessions in the master's, every one
the asset cards name, XAGUSD and the two oils included. Mapping verified against an existing
project block: `knowhow/costs/sessions-live-in-data-db.md`; the 19 blocks already generated:
`~/Desktop/AlgoData/scratch/sessions/ftmo_sessions.xml`. Wire it first: give the builder the DB
(a copy — the master's GUI holds the file) as the fallback source of a session block, with a test,
and set `session:` on the three cards that say `null` (XAGUSD_ftmo, UKOIL.cash_ftmo,
USOIL.cash_ftmo) after confirming with the owner. Then every asset can be built.

## What already exists — use it

- **The queue**: `~/Desktop/AlgoData/scratch/calib_queue/` (`HANDOFF.md`, `queue.sh` v3, `list.txt`
  with one `TIER SYM TF TAG` line per population, appendable while it runs). No agent in the loop:
  build and OOS retest in one custodian start, review overlapped with the next build, each project
  retired when complete, ≈10 minutes and ≈7,000 strategies per population. It must be adapted:
  Simple Strategy instead of the free-shell template, a palette per family, the owner's genetic
  options, `builder --acceptance calibration` instead of its ad hoc filter script, and a family tag
  in the project name. Re-measure the 6-minute box: with a population of 500 × 20 islands a
  generation is 10,000 individuals — check how many generations fit, and size the box so the
  genetic search actually evolves without the databank ever filling (a full databank replaces by
  IS Ret/DD: a selection).
- **The calibration toolkit**: `calib_queue/calib/` (`run.py`, `compare.py`, README) and the
  validation scripts in `~/Desktop/AlgoData/scratch/calib_final/` (`run_all.sh`).
- **The nulls**: `~/Desktop/AlgoData/scratch/null2/` (report, code, per-cell false-positive rates,
  the PF luck formula, the power table, the floating-risk tables). The older
  `null-fpr-2026-10-01` was deleted (wrong statistic): point the toolkit's `--null-root` at `null2`
  or adapt its null join.
- **The red-team review**: `~/Desktop/AlgoData/scratch/calib_redteam/review.md` — what an
  independent recomputation corrected last time. Run a red team again before delivering.
- **Code that now exists**: `assets/_study.yaml` + `core/buildfilters.py` +
  `sqx/projects/rankings.py` (the builder writes the Build's acceptance; `--acceptance
  study|calibration`); step-8 facts for every study; `gate.scorecard.drift_excess_t`, `trade_t`,
  `{is,oos}_trades_per_year`, `{is,oos}_max_dd_r`, `_worst_day_r`, `_worst_trade_mae_r`,
  `_net_per_year_r`, `_dd_over_net_year`; `by:` overrides in `criteria.yaml` per timeframe, symbol
  or asset class (a per-family override does not exist yet — add it if the criteria need it).
- **Knowhow**: `knowhow/research/gate-t-scales.md`, `step6-floor-vs-step8-yield.md`,
  `post-selection-bias.md`; `knowhow/sqx-drive/unselected-build-population.md`,
  `export-after-every-stop.md`; `knowhow/perf/review-path-after-sqx.md`,
  `per-strategy-readings-ram.md`; `knowhow/conditions/build-rankings-acceptance.md`.
- **Prompt for other steps**, with the traps: `docs/AgentPDFs/prompt-criterios-otros-pasos-2026-10-02.md`.

## The design to run

- **Cells:** asset (≥ 10-12) × timeframe (M30, H1) × direction (long, short) × family (only the
  families the asset's card allows) × generation (genetic with the owner's options; a random-
  generation twin on a subset, as the control that says whether a cell is enriched or is chance).
- **Unselected populations:** minimal in-sample acceptance (trades ≥ ~100 on the build window and
  net profit > 0), nothing reading OOS, databank never full.
- **Per population:** Build → OOS retest (step 7, oos1 costs, 1-minute precision, no acceptance
  conditions) → harvest → gate, edgeCost, snoopingScreen, spread (where a scan exists), monkey →
  facts → toolkit. Not feedQuality, profitShape or entryQuality.
- **Then, on the new populations:** redo the step-6 dose-response (trades per year, IS profit
  factor, anything the family makes relevant), the step-8 funnel and each rule's sole effect,
  per family and per asset; the A/B of filters inside the Build against the same cut afterwards
  (last time, inside the Build lost good strategies — one build per arm, so repeat it with
  replicas); and the test nobody has run: a `Trade_`-style build that fills the databank and keeps
  replacing by IS Ret/DD for its full time, against a short one.
- **Questions the family dimension must answer:** does the family the asset card recommends
  actually yield more OOS survivors than chance on that asset (against its random twin and its
  null)? Do thresholds differ by family (trade frequency, holding time, floating risk in R)?
  Which cells show no enrichment at all — those are a finding, not a failure.

## What the first calibration established — the owner's priors

- Statistical significance comes first. He wants **at least 40-50 trades per year**; written
  yesterday as the Pass line (fail < 20, limbo 20-40, pass ≥ 40 on `is_trades_per_year`), because
  as a hard floor it cost 50-63 % of what continued. Re-measure on the new populations and bring
  him the cost again.
- He holds that **profit factor and the Kaufman efficiency ratio are vital**. Measured: PF works
  as a floor, not a selector, and its luck level depends on the trade count; the equity curve's ER
  is the PF under another name; the market's ER before entry did not persist IS → OOS. Re-test
  per family — a trend-following or breakout family may read the market's ER differently.
- Only USDJPY long showed edge; no strategy was individually significant after the search
  (largest trade t 3.57 against ~3.7): step 8 enriches, later steps prove. Pass = proven, Limbo =
  could not be proven yet (goes on, marked), Fail = chance or unbearable risk. A missing fact is
  Limbo.
- Funded accounts first: floating risk in R is its own axis (correlation 0.06 with the t).
- `oos1` of USDJPY and XAUUSD was already read to choose thresholds; this run reads it again on
  the new populations. Say so in the dossier; never touch `oos2`.

## Rules of engagement

- The custodian (`SQX_w2`, 5070) is this team's: one job at a time, start and stop only through
  `bin/sqx-worker.sh`. The conductor takes only the one-shot exports. Never the master. The owner
  has closed the custodian's GUI. `Test_Calib_USDJPY_H1_freeL_ver` (the project he inspected) is
  still on the custodian: retire it first (`python3 -m sqx.projects.retire … --role custodian --yes`).
- Never `pkill -f` / `pgrep -f` (they match your own shell). At most 8-12 parallel Python
  processes, at least 25 GB of RAM free. `/tmp` is 3.9 GB: big files go to `AlgoData/scratch/`.
- A long-lived agent burns tokens re-reading its history: scripts run detached, agents wake on a
  marker file, research and synthesis agents start with a clean context and read from disk.
- Yesterday's populations were deleted on the owner's order (2026-10-02): every `Test_Calib_*` and
  `Test_AB_*` tree under `AlgoData/{reports,harvest,raw,metrics}`. Their small text reports stay
  as the record of the first calibration (`scratch/calib_out`, `calib_synthesis`, `calib_redteam`,
  `calib_final`) — numbers from populations that broke rules 14 and 15. Keep this run's data tidy:
  delete a population's `raw/` once its harvest is written, and tell the owner what it weighs.
- Do not commit. Every task ends with the list of files changed and «¿Quieres hacer el commit?».
  The working tree already holds yesterday's uncommitted work of this study (and other sessions').
- An ambiguity is a question to the owner, never a default (rule 11).
