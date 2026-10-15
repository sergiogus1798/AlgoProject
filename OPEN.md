# Open Issues

Tracked issues for the AlgoProject / StrategyQuant X pipeline.

Status: 🔴 open · 🟡 in progress · 🟠 open, owner's call

**Only what is still to do lives here** (owner, 2026-10-15). Closed issues (⚪ 🟢 ✅) are in
`docs/OPEN-closed.md`, verbatim, numbers preserved; what was done inside an open issue is in git
and in `knowhow/`. The index below lists open issues only.

## Index

| # | status | title |
|---|---|---|
| 19 | 🟡 | Three Monte Carlo thresholds are placeholders |
| 38b | 🟡 | `/plugin` does not exist here — sqx-lab installed by hand, does not auto-update |
| 42 | 🟡 | Three Python entry points were never profiled, because they spend `oos2` |
| 50 | 🟡 | Step 20 is built but decides nothing yet (owner answered C8, not applied) |
| 78 | 🟡 | MetaTrader 5 under Wine: what is still unproven |
| 81 | 🟡 | The window's cut-over (plan 24) left four owner's calls open |
| 84 | 🟡 | What the 2026-09-29 walk of the window left for the owner |
| 85 | 🟠 | Prop-firm funding workstream — the owner's calls still open |
| 86 | 🟡 | Audit 2026-09-30: the master's `ParameterCount` column value |
| 87 | 🟠 | Portfolio construction engine — nothing real has run |
| 88 | 🟠 | SQX's daily curve is each day's LOW equity — readers that difference it |
| 89 | 🟡 | What the 2026-09-30 H1 workflow run (steps 5-26) left open |
| 93 | 🔴 | Criteria of steps 6 and 8 — owner answers of 2026-10-15 to apply, 15 assets unmeasured |
| 100 | 🟠 | Literature scout — owner decisions pending, entries without a condition |
| 104 | 🟡 | Portfolio build 2026-10-05: findings left unfixed |
| 108 | 🟠 | Step 12 redesigned (T0-T4, steps 11.5 and 11.7) built beside the old one |
| 110 | 🟡 | Two-chart strategies: steps 10 and 13 to 18.5 not yet run in SQX on a two-chart mother |
| 112 | 🟡 | Knowhow weekly pass 2026-10-11: one core-count re-measure left |
| 113 | 🔴 | Next batch needing MT5 or the custodian |
| 115 | 🟠 | The harvest cannot record WHY SQX dismissed a strategy |
| 118 | 🟠 | Deferred builder gates: task windows vs segment, second chart in a template |
| 120 | 🟠 | El repreciador no reproduce a SQX en el oro (oos1) |
| 121 | 🟠 | Step 18.5 still skips XAUUSD mothers |
| 122 | 🟠 | Integridad de la investigación: lo que F22 no arregló |
| 123 | 🟠 | Una superviviente de gorilla no llega al paso 26 de leaseWeb (falta la verificación real) |

Read this index, then only the section you need: `grep -n '^## <N>' OPEN.md`.

---
## 19. 🟡 Three Monte Carlo thresholds are placeholders

`portfolio/common/monteCarlo/` (trade-level Monte Carlo) ships the specification's thresholds; three are
not the owner's decision. Owner, 2026-09-29: deferred to the future, not blocking. Measured on the 36
strategies of `XAUUSD/Results` (2026-09-09), they live in `config.yaml` and `gates.py`:

1. `scoring.survival_dd_pct` = 10 % of the account vetoes 21 of 36 alone; a statement about position size
   as much as about strategies. Placeholder until the prop-firm rules fix it.
2. The dead-block veto (any non-overlapping 24-month block with a negative bootstrap median) vetoes 30
   of 36. Alternatives: `portfolio/common/monteCarlo/POSSIBLE_IMPROVEMENTS.md` §1.
3. The Family D sub-score saturates at 0 for every strategy (worst of three parts) and carries no information.

## 38b. 🟡 `/plugin` does not exist here — sqx-lab installed by hand, does not auto-update

`bin/sqx-lab-install.sh` installs it. Left: re-run that script by hand after each vendor update.

## 42. 🟡 Three Python entry points were never profiled, because they spend `oos2`

`walkForwardCorrelation/report.py` (step 17), its `pbo.py` path over `oos2` (step 18) and
`walkForwardMatrix/report.py` (step 19): running them spends the reserved window. Owner, 2026-09-29:
measure them the first time 17-19 run for real, not before. The MC Retest and the SPP cost is SQX's
(~34 h and ~2.8 h), not measured at 500.

## 50. 🟡 Step 20 is built but decides nothing yet (owner answered C8, not applied)

`studies/closing/blindJoint/`. `joint.pieces` is null in `config.yaml` (owner, 2026-10-12: nobody is
discarded at step 20). **Contestado 2026-10-15 (encargo 72, C8 A): manda el 65, se borra `sin_fallo`;
falta aplicarlo** (`sin_fallo` still lives in `studies/closing/blindJoint/{readings.py,config.yaml,tooltips.py}`
and `assets/_policy.yaml:47`). Still open: whether an autonomous agent (`ALGO_AUTONOMOUS=1`) is held
out of oos2 for BlindJoint (not in `reserved_for`). Owner's look at the USDJPY mothers' oos2 daily P&L on
2026-09-26 left no ledger row: his call whether to add one. Part V of encargo 48: a real variant batch
with `variant_trades.parquet` has never been produced, so the real read in
`studies/optimisation/wfc/inputs/batch.py`, the export in `pipeline/autopilot/variants.py`, the build ->
oos1 rehearsal of `studies.optimisation.wfc.calibrate` and the window's WFC and parameter-cloud zones are
unverified on real data; the first oos2 read by step 17 must be the real blind block, never a test.

## 78. 🟡 MetaTrader 5 under Wine: what is still unproven

mt5/ exists (tester, verify, reconcile, fleet) and step 26 is built (`mt5/verify/README.md`, encargo 55).
Still open: the MetaQuotes MCP tester is unproven (until a real run shows its report carries every
deal, `mt5/tester.py` + `mt5/report.py` stay); the tester cannot pass EA inputs (`[TesterInputs]`); the
news filter's live close on a demo chart, the EAs in `AlgoData/mt5/eas/` regenerated 2026-10-02 only in
AlgoData (`Experts/` and the live charts carry the old ones), the thin-day exclusion in a tester run
(`knowhow/mt5/ea-news-filter.md`); FTMO-Server4 lacks USDJPY M1 for 2023-09-20→2023-11-10
(`knowhow/mt5/mt5-tester-m1-gaps-hide-news-window.md`). The `weeklyReconciler` (`mt5/reconcile`) is encargo 72
part C (pending). `Bash(*)` is allowed here, so the `.claude/settings.json` deny list of MetaQuotes' `trade_*`
tools does not stop a hand-made HTTP call; the terminal's own «prohibit AI trading» option is the lock.

## 81. 🟡 The window's cut-over (plan 24) left four owner's calls open

(Item 1, the USDJPY ledgers, is done.) His to say:
1. «Subprueba del MC Retest»: F5 built a re-run of one trade-level Monte Carlo test or one crossmarket
   market beside the stored result (`knowhow/eng/partial-reruns-beside-stored.md`). Did he mean that, or
   one of the eight SQX MC Retest perturbation tasks (an SQX run)?
2. «Archivar» (F4) asks the step with no default, because the rail's last «hecho» can be a reading past a
   sealed 17-19. Keep it without a default, or name the rule.
3. Knobs applied as recommended (Q4, Q5 show «0» where Min Distance is `null`, Q15 filters AND only,
   Q17 Configuración SQX writes `_build.yaml` for new projects): he corrects them if wrong.
4. F7's live test: «Continuar workflow» is tested with every SQX call faked (`tests/test_advance.py`,
   `test_advance_edges.py`); the live run on the conductor with `Test_UiContinuar_USDJPY` (Q20) has not
   happened (plan 24 §6).

## 84. 🟡 What the 2026-09-29 walk of the window left for the owner

Still open (owner's rulings of 2026-09-29: MCR 3's slippage stays at half the spread, and our tool never
clears a databank before a retest — the launch warning stays):
- Steps 10.5 and 16.5 have no button (the /crosstf and /variants fabrication: mothers to pick and a
  clamped/rounding review), so 11 and 16.5-18.5 cannot be run from the window.
- Estrategia needs ~1,480 px of width: it fits 1920, not 1280. A redesign, not a fix.
- The interview asks «transición o estado» after a sentence that says «cruza»; it could infer it.

## 85. 🟠 Prop-firm funding workstream — the owner's calls still open

Catalogue, deals, economics (encargos 33, 34, 54) are built (`portfolio/funded/`); NOTHING real has run: no
real pool, no real-root bank table, no oos2 read. Owner's answers of 2026-10-15 are in encargo 72
(F2: taxes optional, `owner.tax_rate` null = off, encargo 73; F3 A: 5 % `p_payout_denied` PER PAYOUT;
V1: FTMO 541350656 is a real funded account that already paid a payout, FundingPips 11308943 is in
phase 2 of 2, Hantec 8063673 in phase 1 of 2). Open, the owner's:
1. **FundedNext** (candidate): the EA usage fee's amount; one account per portfolio (identical trades
   across accounts are banned); gates G3 Spain and G4 payout record; then activate or not —
   `docs/AgentPDFs/fondeo-admision-fundednext-2026-10-14.md`.
2. **FundingPips** (candidate, blocked): may a self-built SQX EA trade? Ask support. If yes, confirm the 8
   typed prices and rules (`AlgoData/funding/manual/fundingpips.yaml`, `confirmed: false`).
3. **Support questions S1-S6** (the owner sends them): FTMO 2-Step fee refund per account (modelled as NO
   refund, `rules/ftmo.yaml fee_refund=false`, unconfirmed); Hantec fee refund and whether «Profit Target
   -2 %» lowers every phase (modelled phase 1 only); Hantec's prohibited-strategies article.
4. `portfolio/DECISIONS.md` #11, the remainder: with `oos2` spent, what validates the chosen combination
   (the firm-feed period, a live incubation, nothing).
5. The rest of encargo 33 §6 (risk per phase, which `h` to show).

To build / verify: a test of Hantec's price formula against its page's JS; Hantec's commission on gold is
unconfirmed, so the verification refuses Hantec on XAUUSD until it is filled in the Activos zone.
Known limits: the deal notification only shows if the desktop session is up at 10:00; FundingPips'
catalogue is typed (its site blocks automated reading); codes of firms without a public check stay `unverified`.

## 86. 🟡 Audit 2026-09-30: the master's `ParameterCount` column value

Left: `Build-Task3.xml` of the master's projects AUDJPY, EURUSD and USDJPY still carries a `ParameterCount`
column value, which removing the custom class may break. The owner's call (master rule: never edit there
without his word).

## 87. 🟠 Portfolio construction engine — nothing real has run

Plan `portfolio/PLAN.md`; order in `portfolio/CLAUDE.md`. M0-M9 and F1-F5 are built and tested on the
relaxed `Test_nikkei_ref` pool under a quarantined TEST root; no real pool run, no portfolio run or ledger
row in the real root, M9 incubation not running, no real oos2 read. Waits on:
- **A real pool.** The 30 mothers of `Test_USDJPY_donchianUpperCrossUp_H1` are archived (none carries a
  stop, no pool declared); `candidates.py` lists 182,464 commands, 182,220 of them `Test_Calib_*` (not
  archived). Pool's extent is the owner's. Sizing still depends on a per-trade stop: see #113.
- **Contestado 2026-10-15 (encargo 72), falta aplicarlo** (A2): `wf.confidence` F4 B (Bonferroni over the
  arms, ≈ 0.99 per arm); incubation F5 `figure: pnl`, `history: [build, oos1, oos2]`, `band: [5, 100]`
  (all four still `null` in `portfolio/common/construct/config.yaml:67-73`); F6 A (M0 pool without
  `Test_Calib_*` and anything built with costs before 2026-10-01); F7a, c, d, e confirm, **F7b change: the
  open-risk cap must count the trailing max loss**, F7f leave. `open_risk_cap` (0.5) and
  `verdict.pass_percentile` (0.95) are set since 2026-10-14; `t1_gap` since 2026-10-15.
- Readings the Council's answers leave open: `portfolio/PLAN.md` §12 «Readings the Council's answers leave open».
- Hantec's server clock is UTC+3 today (beacon); EETUS/EET distinction applies between 25-10 and 1-11.

## 88. 🟠 SQX's daily curve is each day's LOW equity — readers that difference it

`dailyEquity.bin` holds the day's lowest equity (closed P&L plus open positions at their worst M1 wick);
M1 rebuild matches 100 % of 3,983 days, MTM close 45 % → `knowhow/sqx-format/daily-equity-bin.md`. Readers
that difference it are low-to-low: `studies/screening/snoopingScreen/` (reads the close-to-close curve since
2026-10-04), `studies/closing/blindJoint/` (same code, refuses its SPA until step 16.5 harvests
`trades.parquet` per variant), the CSCV (PBO 0.37→0.35, 0.36→0.39, 0.40→0.52 on a rebuild; needs trades
per variant). Waiting on the owner: harvest trades per variant at 16.5 for the CSCV? Owed: `search/stageb_data.py:62`
calls `minute_path` without the commission; universe caches built before 2026-10-04 must be rebuilt; the
PercentageBased branch is unverified; a perf target for `closecurve`; decay t = 0.78-0.88× close-based, use
`drift_excess_t`; exposure is document-only. Card: `knowhow/sqx-format/equity-reconstruction-usdjpy-gap.md`.

**2026-10-15.** Revisado: los tres lectores que nombra ya no diferencian la curva baja. snoopingScreen (hoy engines/inference/snooping) y blindJoint leen cierre a cierre con closecurve (studies/closing/blindJoint/inputs.py:panel, test tests/test_close_curve.py); el CSCV pesa desde variant_trades.parquet (studies/optimisation/cscv/inputs/batch.py:read), que el 16.5 ya cosecha (pipeline/autopilot/variants.py:186) - la pregunta del dueño sobre cosechar operaciones queda contestada por el código. stageb_data ya pasa la comisión a minute_path (stageb_data.py:102). Siguen leyendo la curva baja a propósito y documentado: gate (measures.py:23, inputs.py:293; los *_max_dd_r y *_worst_day_r son flotantes) y decay (decay t 0.78-0.88x, usar drift_excess_t). Pendiente: rama PercentageBased sin verificar, objetivo de perf de closecurve, cachés de universo anteriores al 2026-10-04 por reconstruir.

## 89. 🟡 What the 2026-09-30 H1 workflow run (steps 5-26) left open

Run on `Test_USDJPY_donchianUpperCrossUp_H1`. Still open:
- **MC Retest ingest**: two level tables unusable, «run cut short» — `bar/4.3.53`, `ohlc/8.13.72`
  (`knowhow/sqx-drive/mcr-nullpointer-fastutil-transient.md`).
- **Step 23 control «madre reconstruida»** printed an empty table (mothers from `CrossTF_Mothers` keep no
  build/oos1 result to compare against). Step 23 was deleted 2026-10-11 (#113): check whether it still applies.
- **A study whose result lives in another databank reads «Sin resultado todavía»** on every other
  databank's strategy page (Lectura conjunta filed under `WFM`, Exposición under `CrossTF_Mothers`, Stop
  loss ATR and the optimisation studies). Results pair by identity; a name pairing is only offered as a
  jump (`ui/daemon/runner/offer.py`), today only for a study the runner refuses. Proposal for the owner:
  offer the same jump when the study is not refused but its result is elsewhere.
- **Filtros candidatos asks for ≥200 strategies**; after the step-8 cut the population is 60.
- **Hantec after the clock fix still fails rows 1/3a/5** on the three USDJPY mothers (drawdown 0.292 % SQX
  vs 0.228 % MT5 on 10.9.72): not the clock (`clock_h` 0 on all six) — costs or Hantec's history, to diagnose.

## 93. 🔴 Criteria of steps 6 and 8 — owner answers of 2026-10-15 to apply, 15 assets unmeasured

`assets/_study.yaml` (step 6) and step 8 of `pipeline/autopilot/criteria.yaml` carry an agent's PROVISIONAL
proposal (`docs/AgentPDFs/criterios-implementados-2026-10-12.md`). Owner, 2026-10-04: the calibration
study they came from ran at a wrong spread and was deleted: do not sign or build on those figures; they
need a new calibration at the recalibrated spreads or his own numbers. **Contestado 2026-10-15
(encargo 72, «toma todas tus recomendaciones»), falta aplicarlo** (the other instance, with 49/50/53):
C1 (α 0.01, done 9aef247), C2 A limbo, C3 A, C4 A (step 6 figures signed as provisional v0), C5 A `dev.on`,
C6 A exit rule, C7 A clock-block list, C9-C11 A. Still open:
- Trades-per-year floor (written fail < 20, limbo 20-40, pass >= 40; he prefers 40-50) and the risk per
  trade on funded accounts, if not covered by the answers above.
- None of the 17 assets added 2026-10-02, except DAX40 (it ran, `Test_DAX40_*`), has been RUN in SQX.
- No Simple Strategy project has been confirmed by a real SQX population (`knowhow/authoring/simple-strategy-build-xml.md`).
- A template's fixed idea is a hole bound to a one-item group, and SQX has one condition range per side: a
  side is written 1..1, not 0..1. Whether a bound hole at min 0 keeps its block needs one short build; until
  then «the idea alone» is never built from a template.
- A `Trade_` build fills the databank in minutes and then replaces by IS Ret/DD for the rest of 180 min
  (selection nobody measured: 180-min full build against a 6-min one). The A/B of floors inside the build is one build per arm.
- Not a fact yet: the IS profit factor (a `PF >= 1.10` rule needs it). `oos1` of USDJPY and XAUUSD was read
  to choose the thresholds; freeze them before the next build. `oos2` untouched by the calibration except one look.
- Long builds (180 min, cap 10,000) with a full databank: no IS filter tested; `drift_excess_t` correction
  proposed, not applied; `wfc.py` gives extra markets the main's dates; 7-11 % of strategies change identity
  between build and OOS databank (name join; fingerprint agrees 99.7-100 %); the crossmarket and crossTF
  studies hard-code their window; `assets/_policy.yaml` oos2 end 2026-09-30 is past the last bar of XAUUSD,
  XAGUSD and HK50 (`knowhow/sqx-drive/cannot-start-unresolved-past-data.md`); 31 H1 base cells have no oos2.
- The 28 calibration populations used the broad palette (842 blocks): rebuild per family.

## 100. 🟠 Literature scout — owner decisions pending, entries without a condition

`studies/research/literature/`, `/literature-scout`, `bin/daily-literature-scout.sh` (cron `0 7 * * *`;
opus reads, sonnet triages, `run.budget_tokens` 3M is a runaway guard). Open:
- Entries wait on his answer (`python3 -m studies.research.literature.report`, `PREGUNTA` blocks, `--answer ID N`),
  then a session writes their measures (`scout measure`). The questions outgrow what he can answer: should the reader ask less?
- Entries without a measure: most state no parameters (five point to Sullivan et al. 1999), one tests a
  354-pair grid, the newest need conditions `rules.py` lacks (Keltner, Hull, MACD, ADX).
- OpenAlex has a free daily budget per IP; a free API key would lift it (the owner's to get). traders.com,
  SSRN, Alpha Architect and Semantic Scholar refuse a script.
- The profile's top-up was stopped half-way on 2026-10-02: only DAX40 and DJ30 carry TR-65's six measures
  and the three corrected ones; `measures.csv` and `assets/FAMILIAS.md` may still show the old rows (not
  re-checked). Complete with `nice -n 19 python3 -m studies.research.marketProfile.report --top-up`, then `--familias`.

## 104. 🟡 Portfolio build 2026-10-05: findings left unfixed

1. **Sizing takes the latest archived version, not the pool's frozen `identity@version`**
   (`portfolio/common/construct/funded.py:42,64`, `funded_b.py:85`, `inputs/pool.py:184` call
   `archive_read.versions(identity)[-1]`). **Contestado 2026-10-15 (encargo 72, F8a): arreglarlo, que lea la congelada; falta aplicarlo.**
2. **The GA's rank score saturates above `real.exhaustive_max`** (now 1,000,000): `real.rank_reference: seeds`
   ranks against greedy cliques, so better than all of them scores 1.0 and the GA stops without trying small K
   (planted pool returned {A, B, N0, N1, N3} where exhaustive gives {A, B}). F7f: leave until a real pool passes the limit.
   The funded GA also re-evaluates duplicates (4,500 evaluations = 58 distinct of 103) and counts them in the ledger's `n_scored`.
3. **`funded_b` reruns give different winners** (three runs, finalists within 0.003). Folders are no longer
   overwritten (`core.manifest.fresh_dir`). **Contestado 2026-10-15 (F8b): guardar la semilla en el manifiesto y una carpeta por corrida; falta la semilla** (none recorded yet).
4. **`tests/test_portfolio_build.py` fails** («Ningún miembro del pool concilia con SQX»), set aside in
   `tools/audit_tests.py`. Nothing archived reconciles under today's conditions (the 15 mothers with a harvest
   reconcile 0.92-0.99, MAE/MFE licence 0.73-0.97 against a 0.99 floor; feed-clock mismatch of archived stamps
   suspected). Owner (2026-10-05): run on today's conditions, no re-stamping shim, no skip. **Contestado 2026-10-15 (F8c): archivar una estrategia nueva cuando la corrida limpia dé una superviviente.**
5. pyarrow 25.0.1 `pd.read_parquet` aborts at exit under load (178 call sites, no shared reader; planted-pool
   tests use `pa.set_cpu_count(1)`): `knowhow/eng/pyarrow-read-parquet-aborts-at-exit-under-load.md`. Project-wide choice open.

**2026-10-15.** Puntos 1 y 3 hechos (encargo 72 F8a/F8b): `funded.frozen_versions(pool, cfg)` da identity -> versión congelada y `size_members`, `_member_meta`, `real.py` y `funded_b.load` la leen en vez de `versions()[-1]` (sin pool, p. ej. `incubation/run.py`, sigue la última); la etapa B escribe `stage_b_seed` en el manifiesto y ya tenía carpeta por corrida (`funded_b.target`). Tests en `tests/test_portfolio_verdict_funded.py`. Punto 4 (F8c): archivar una estrategia nueva cuando la corrida limpia dé una superviviente; no se hace ahora. Quedan abiertos el 2, el 4 y el 5.

## 108. 🟠 Step 12 redesigned (T0-T4, steps 11.5 and 11.7) built beside the old one

Encargo 47 (`docs/encargos/47-paso-12-otras-temporalidades-pico-aislado.md`) parts K, F, S, P, D done
without SQX. The live rule is still `crossTF.combined.z_new`; parts V (validation, the cut) and B (deleting
the old reading) wait for the first real run and the owner's «corta».

**Only SQX can verify (part V):** the phase-2 tasks `CrossTF <TF> build` write their databanks
`CrossTF_<TF>_build`; whether a re-run overwrites or appends; periods doubled on M15 (M30 mothers) accepted
by every indicator; `k / c` with c < 1 may exceed a block's `maxValue` (PMax 10.99 → 15.6 on M15); the cost
in time of phase 2 (proposal §8.5); `z_delta` and `z_build` centred on 0 with real edgeless mothers (§8.7);
`apply_verdict` on `CrossTF_Input` at 11.5; a re-run of 11.5 may read a stale `CrossTF_<TF>_build` export.

**Owner decisions pending:** K-1 the R of `ret` (each timeframe's own, as implemented, or the mother's via
`c`); K-2 a lone measured neighbour that fails T2a or T2b (NO PASA, or LIMBO as implemented); K-3 the window
of T4 (the mother's bar, as implemented, or the slower); `CBlock_CandleBreakoutLong*.Double2` («body > Mult ×
ATR»): `bar` or a ratio `other` (today `unverified` in `sqx/variants/ranges.yaml`).

## 110. 🟡 Two-chart strategies: steps 10 and 13 to 18.5 not yet run in SQX on a two-chart mother

`sqx.projects.charts` writes the second chart into every task (`knowhow/sqx-drive/mtf-template-needs-three-charts.md`).
Proved in SQX 2026-10-09 (`filterMALong`, EURUSD M30): build, OOS, step 8's readers, the step-12 scaling, step 26.
Not proved: steps 10 and 13 to 18.5 on a real run (the ten strategies of that build lost out of sample and
step 8 kept none). The first two-chart mother to pass step 8 is the first real run of those tasks: read its
SQX log for `requires 2 charts` if one aborts.

## 112. 🟡 Knowhow weekly pass 2026-10-11: one core-count re-measure left

`knowhow/perf/server-cores-and-ram.md` still says «Xmx108g» in its `kw:` and body (heaps are 24/16/80 g,
`perf/ram-budget`). Re-measure the core counts on leaseWeb before editing it: DEFERRED until the machine is
free (a null run is running); do not measure before.

## 113. 🔴 Next batch that needs MT5 or the custodian (owner, 2026-10-11)

Steps 22, 23, 24 were deleted, step 25 left the chain, step 21 only describes, step 20 cuts DESCARTAR
against a random trader with the same footprint (dossier `docs/AgentPDFs/medicion-stop-lejano-2026-10-11.md`).
- **(1) Portfolio sizing still depends on a per-trade stop — design task.** Strategies trade with no stop, yet
  `portfolio/common/construct/inputs/risk.py` sizes from a grafted ATR stop (`sqx/variants/build/stoploss.py`,
  ledger key `portfolio.funded.stop_percentile`). At the exported size ~50-77 % of simulated 100k accounts
  breach a firm limit. Next: size by the admissible floating daily loss and cap the joint exposure.
- **(a) Step-26 calibration.** One reference run per asset × firm with a trivial strategy, to set
  `mt5verify.exit_same_min` and `mt5verify.trades_min` (provisional). After it: rows 3b/4 relative to the
  mean daily |P&L|, SQX spread from history instead of an instant, MT5 equity drawdown, pool moved to `portfolio/inputs/pool.py`.
- **(b) No-edge calibration of 18 / 18.5 / 19.** A population with no edge through those steps, as step 17's calibrate did.
- **Leftovers.** Empty `stop_percentile` / `stop_x` columns in the pool and campaign CSVs. edgeCost's
  `--strategy` mode stays because ~55 old result folders would otherwise be read by step 8.
  `portfolio/common/construct/candidates.py:26` still names `worth_it` in `SURVIVOR_WORDS`.

## 115. 🟠 The harvest cannot record WHY SQX dismissed a strategy

Decisión pendiente del dueño. 🔬 En `Test_NIKKEI225_M30_simpleL_fin`, `_val` y `Test_USDJPY_M30_doubleROCLong` el bitmask `StrategyProblems` del fichero de build es 0 en toda estrategia sin gemela OOS (300 muestreadas en cada uno); la razón vive en el fichero retestado, que es el que falta. `missing_oos.csv` ya tiene la columna y la cosecha imprime un aviso en mayúsculas; NO está activado un paro por «gemela ausente sin explicar». Para activarlo hay que leer la razón de SQX antes del descarte (`AutomaticDismissal` de la tarea Retest, 10 códigos, heredados del donante). Ficha: `knowhow/sqx-format/dismissal-reason-not-on-build-file.md`.

## 118. 🟠 Deferred builder gates: task windows vs segment, second chart in a template

**Contestado 2026-10-15 (encargo 72, L3): (a) ya, (b) cuando aparezca la primera plantilla de dos gráficos; falta aplicar (a).** (a) ningún gate comprueba que la ventana de cada tarea coincida con su segmento (`registryxml.clip` ya imprime lo que recorta); (b) ningún gate rechaza una plantilla con un segundo gráfico.

**2026-10-15.** 2026-10-16: (a) hecho — sqx/projects/resources.py::refuse_off_segment, llamado desde builder.build tras configure y antes de wf.finish; (b) espera a la primera plantilla de dos gráficos

## 120. 🟠 El repreciador no reproduce a SQX en el oro (oos1)

Hechos en `knowhow/research/monkey-reprice-audit.md` y `knowhow/research/price-rounding-per-asset.md`. `price_rounding` por activo está hecho (encargo 70, p70e PASA); el oro en oos1 sigue con descuadre 0,11-0,18 (> 0,01) y el 18.5 salta sus madres (`pipeline/autopilot/blind.py`, `skipped`); el resto de −0,043 USD/operación es dispersión sub-tick de las barras de SQX, no reproducible (aceptado). Sin verificar contra SQX: stop-loss corto, salidas por profit target, comisión PercentageBased. El `variant_trades.parquet` de 10k de USDJPY es anterior al commit c443f1d y mezcla 16 símbolos bajo `Main`: regenerar. 22 fichas sin `price_rounding` (el repreciador se niega) hasta medirlas (P1 A).

## 121. 🟠 Step 18.5 still skips XAUUSD mothers

Same matter as #120 (written in English from a scratch log). The gate now has its own key `marketSurfaces.sqx_off_share` (0.01); gold oos1 stays at 7-22 % off-share, so 3 XAUUSD mothers are skipped in p70e («18.5 saltado por descuadre» counts as a result, not an error in the functional test: owner R18c A). Cause: the card's slippage of 4.67 points is not a tick multiple and SQX splits fills over two ticks; with `none` the residual is the sub-tick noise of #120. Trap: the ledger key `wfc.sqx_gap_relative` means a fraction of NetProfit in `engines/weekly/panel.py:119-122` but a share of variants in the 18.5 gate. Owner's open call: what to do with gold at 18.5 (accept the skip, or measure the gate differently).

## 122. 🟠 Integridad de la investigación: lo que F22 no arregló

Origen: encargo 68 F22, 2026-10-14. 🔬 Cada punto es una decisión del dueño o necesita su confirmación.

- **Segmento inferido en el ledger.** `judge.py:115` asigna `oos1` cuando un paso no declara segmento; el dueño debe declararlo en `criteria.yaml`.
- **Cinco filas de `log_cut`** suponen segmento `oos1`, y `monteCarlo` supone el paso 20. A confirmar.
- **Procedencia que no se guarda.** `testroot` tiene la bandera `pseudo_oos2`; `core/study/result.build` no registra proyecto ni ruta/hash del harvest; los escritores de `verdict.csv` y `panel.parquet` no dejan un meta al lado.
- **Nombres.** La clave `"oos"` de la puerta llama así a lo que no siempre es el OOS; el candidato del ledger de `replication`, `monkeyExcess` y `funded/decide` tiene el mismo problema.
- **Verdad de un flotante.** Guardas `if x:` sobre un flotante en `attribution`, `crossTF` y el estadístico de `crossmarket` (un 0.0 legítimo cuenta como falta); `== 0.0` en `portfolio/funded`.
- **Alineadores sin test de una barra:** `occupancy`, equity/excursiones de `portfolio`, `mc/units`, celdas de `crossmarket`, `touch` de `feedQuality` y `dataquality`.
- **Monkey `on_grid` frente a `reprice.located`:** difieren en una barra. Alinearlos movería resultados del mono ya guardados; fijado por un test. Decide el dueño.
- `F401` y `B904` entran en el `select` de ruff en cuanto se comiteen `portfolio/testroot/harvest.py`, `tests/test_autopilot_closing.py` y `tests/test_perf66_review_data.py` (del encargo 66). El número de supervivientes del 17 puede variar al repetir: cada corrida debe registrar su semilla (añadirlo si hoy no).

## 123. 🟠 Una superviviente de gorilla no llega al paso 26 de leaseWeb (falta la verificación real)

Hecho 2026-10-15 (encargo 72 D-1 = A): `bin/remote.sh gorilla collect <PROYECTO> [--dry-run]` (`core/store/collect.py`, `tests/test_gorilla_collect.py`, cap. 109). PENDIENTE: la verificación real, que necesita la primera superviviente guardada en gorilla; y que la finalista del paso 26 apunte a `store/<celda>_gorilla/<carpeta>/strategy.sqx` (`mt5/verify/autopilot.py:36-38` pide el `.sqx` en la ruta absoluta de la finalista). No trae `structural/<P>/mothers` ni `autopilot/<P>/<run>/` (fuera de D-1).

