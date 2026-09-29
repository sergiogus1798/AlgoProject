# Open Issues

Tracked issues for the AlgoProject / StrategyQuant X pipeline.
Split out of `CLAUDE.md` on 2026-09-02 so the always-loaded instructions stay lean.
Migrated into the rebuilt project on 2026-09-03; paths updated to this tree.

Status: 🔴 open · 🟡 in progress · 🟠 open, owner's call · 🟢 resolved · ✅ done · ⚪ closed / won't fix

**Closed issues (⚪ 🟢 ✅) live in `docs/OPEN-closed.md`, verbatim, numbers preserved** — this
file (2026-09-29 cleanup) keeps only open sections plus the full index below, so a
"what is broken" read no longer pulls in ~33 KB of settled history.

## Index

| # | status | title | where |
|---|---|---|---|
| 1 | ⚪ | Databanks shrink between sessions — CAUSE FOUND | docs/OPEN-closed.md |
| 2 | ⚪ | ~1,208 `SPP OOS` + ~1,142 `WFM` XAUUSD strategies lost — CLOSED, accepted | docs/OPEN-closed.md |
| 3 | ⚪ | `Infinox_SP500ft_H4_HighPrecision` never loads — WON'T FIX, owner's decision... | docs/OPEN-closed.md |
| 4 | ⚪ | Projects are older than the app — measured, restamping is GUI work | docs/OPEN-closed.md |
| 5 | ⚪ | Mojibake Windows path in task configs — decoded, closed as dead metadata | docs/OPEN-closed.md |
| 6 | 🟢 | SQX logs pruned to 14 days — archived | docs/OPEN-closed.md |
| 7 | 🟢 | `core.sqxfile` has a golden test | docs/OPEN-closed.md |
| 8 | ⚪ | Migrated analyses from the old project — CLOSED 2026-09-26 | docs/OPEN-closed.md |
| 9 | ⚪ | Nine projects ARE ignoring their strategy templates — confirmed, fix is the o... | docs/OPEN-closed.md |
| 10 | 🟢 | The pipeline maps count disabled tasks as live — issue 1's table is overstated | docs/OPEN-closed.md |
| 11 | ⚪ | `XAUUSD_Breakout_H1` depends on the worker's template directory | docs/OPEN-closed.md |
| 12 | ⚪ | Results cited in `knowhow/` cannot be reproduced from the current data root | docs/OPEN-closed.md |
| 13 | 🟢 | Two analyses state conclusions their samples do not support | docs/OPEN-closed.md |
| 14 | ⚪ | The per-project pipeline maps are retired, format undecided | docs/OPEN-closed.md |
| 15 | ⚪ | Layout renamed — `1_sqx/` etc. are now `sqx/` etc. — CLOSED | docs/OPEN-closed.md |
| 16 | 🟢 | The trade-dedup gap now spans four live reports | docs/OPEN-closed.md |
| 17 | 🟢 | Every strategy that already exists carries the OLD `Param Count` | docs/OPEN-closed.md |
| 18 | ⚪ | `EdgeDecayRatio` / `EdgeDecayFilter` retired — waiting on the GUI to unwire it | docs/OPEN-closed.md |
| 19 | 🟡 | Three Monte Carlo thresholds are placeholders | OPEN.md |
| 20 | 🟢 | `.claude/settings.json` gates one destructive repair script but not the other... | docs/OPEN-closed.md |
| 21 | ⚪ | `bin/sqx-worker.sh` keeps half the project off Windows | docs/OPEN-closed.md |
| 22 | 🟡 | `studies/transfer/crossmarket` — state of play after the 2026-09-14/15 rebuild | OPEN.md |
| 23 | 🟢 | The XAUUSD robustness protocol is half built | docs/OPEN-closed.md |
| 24 | ⚪ | The holdout pre-registration — CLOSED 2026-09-26, the owner declined it | docs/OPEN-closed.md |
| 25 | 🟢 | The authoring chain is proven headless end to end — issue 9's positive control | docs/OPEN-closed.md |
| 26 | 🟢 | `PercentageBased` is charged ONCE per trade — settled 2026-09-27 | docs/OPEN-closed.md |
| 27 | 🟢 | Sixteen of seventeen assets have no agreed cost, and the schema changed under... | docs/OPEN-closed.md |
| 28 | 🟠 | `DAX40` has an asset file but the master configures no such feed | OPEN.md |
| 29 | 🟠 | Six index assets have no IS/OOS window, and `SP500ft`'s feed does not exist | OPEN.md |
| 30 | ✅ | `sqx.data.update` ran end to end on 2026-09-25 | docs/OPEN-closed.md |
| 31 | ⚪ | Revisión completa del proyecto — 2026-09-22 — CERRADO 2026-09-26 | docs/OPEN-closed.md |
| 32 | 🟢 | El custodio no tiene candado de propietario | docs/OPEN-closed.md |
| 33 | 🟢 | `pipeline.cleanup` refuses the one finished mother: `metrics.parquet` no long... | docs/OPEN-closed.md |
| 34 | 🟢 | `sqx.projects.builder` installs the donor clone before it refuses | docs/OPEN-closed.md |
| 35 | 🟢 | `sqx.projects.builder --symbol` does not change the market — it cannot author... | docs/OPEN-closed.md |
| 36 | 🟢 | Unit conversions in `no_forex` cost files swing ~5× with the reference price... | docs/OPEN-closed.md |
| 37 | 🟢 | `studies/breakage/mcRetest/` assumes all eight MCR tasks always ran | docs/OPEN-closed.md |
| 38 | 🟢 | Tres divergencias declaradas de los pasos 15, 16.5 y 19 — decisión del dueño | docs/OPEN-closed.md |
| 38b | 🟡 | `/plugin` does not exist here — sqx-lab installed by hand, does not auto-update | OPEN.md |
| 39 | ✅ | El WFC en tres tramos — hecho el 2026-09-24 | docs/OPEN-closed.md |
| 40 | ✅ | Los databanks del proyecto WFC hay que crearlos a mano — resuelto 2026-09-25 | docs/OPEN-closed.md |
| 41 | 🟢 | Half the variant budget goes to combinations that barely trade | docs/OPEN-closed.md |
| 42 | 🟡 | Three Python entry points were never profiled, because they spend `oos2` | OPEN.md |
| 43 | 🟢 | A retest drops the `<!--variant_id-->` stamp — the file name is the only join... | docs/OPEN-closed.md |
| 44 | 🟢 | The CSCV puts two months of `oos1` P&L on its OOS side — each leg's curve sta... | docs/OPEN-closed.md |
| 45 | 🟢 | `nulls.seed` no fija nada | docs/OPEN-closed.md |
| 46 | ✅ | Step 18.5 reads `oos2`, step 23 does not — owner, 2026-09-26 | docs/OPEN-closed.md |
| 47 | ✅ | The conditional map has trading sessions — owner's hours, 2026-09-26 | docs/OPEN-closed.md |
| 48 | 🟢 | Loose ends of the 2026-09-26 batch — each the owner's word, none blocking | docs/OPEN-closed.md |
| 49 | ✅ | Periodic review jobs added — knowhow, dependency map, audit/, docs health — 2... | docs/OPEN-closed.md |
| 50 | 🟡 | Step 20 is built but decides nothing yet — three owner's calls, and 17-19 do... | OPEN.md |
| 51 | 🟢 | The study viewer cannot reach cloud, wfc and cscv — they write into the varia... | docs/OPEN-closed.md |
| 52 | 🟢 | Every stored crossmarket result reads stale in the window | docs/OPEN-closed.md |
| 53 | 🟢 | `edgeCost`'s verdict.csv has no identity column | docs/OPEN-closed.md |
| 54 | 🟢 | A partial re-run (`only`) is not merged beside the stored result — it replace... | docs/OPEN-closed.md |
| 55 | 🟢 | The custodian pulse shows no progress for runs started outside the window — f... | docs/OPEN-closed.md |
| 56 | 🟢 | The nightly audit and docs agents did not run for 16 days — fixed, running ag... | docs/OPEN-closed.md |
| 57 | 🟢 | Step 10 (`crossmarket`) priced exports on the wrong bars and left out the ent... | docs/OPEN-closed.md |
| 58 | 🟢 | A strategy's identity changed in place after the MC Retest — fixed 2026-09-27... | docs/OPEN-closed.md |
| 59 | ⚪ | MC Retest spread and slippage barely perturb forex at today's provisional cos... | docs/OPEN-closed.md |
| 60 | 🟢 | `template_check` no longer checked the owner's condition — fixed 2026-09-27 | docs/OPEN-closed.md |
| 61 | 🟢 | The parameter cloud could not read `collect`'s panel — fixed 2026-09-27 | docs/OPEN-closed.md |
| 62 | 🟢 | `stoploss.graft` needed `key=` to be the first attribute — fixed 2026-09-27 | docs/OPEN-closed.md |
| 63 | 🟢 | Minor frictions of the 2026-09-26 USDJPY M30 workflow run — fixed 2026-09-27 | docs/OPEN-closed.md |
| 64 | 🟢 | `export_spp.py` never manifests the `strategies/` copies | docs/OPEN-closed.md |
| 65 | 🟢 | `snapshots/` disk budget nearly doubled in one night, `profiling/` pinned at... | docs/OPEN-closed.md |
| 66 | 🟢 | `sqx-worker.sh stop` gave up at 20 s while the JVM was still saving — fixed 2... | docs/OPEN-closed.md |
| 67 | 🟢 | `pipeline/XAUUSD/Strategy_17-9-39` no longer runs in the CSCV | docs/OPEN-closed.md |
| 68 | 🟢 | `stress.simulate` reservaba 816 MB por mercado — troceado 2026-09-25 | docs/OPEN-closed.md |
| 69 | 🟢 | La tarea del paso 10 es una estrategia, y debería ser una estrategia-mercado | docs/OPEN-closed.md |
| 70 | 🟢 | El lote del paso 10 no deja ver por dónde va | docs/OPEN-closed.md |
| 71 | 🟢 | `benchmark=0` is the wrong null for PSR, in three finished studies | docs/OPEN-closed.md |
| 72 | 🟢 | `crossmarket` already computes the answer to a question it does not ask | docs/OPEN-closed.md |
| 73 | ⚪ | Three global `sqx-lab` skills are retirement candidates — owner's call | docs/OPEN-closed.md |
| 74 | 🟢 | Steps 23, 24 and 25 export into the same `raw/<P>/WFC_*/<day>/` and overwrite... | docs/OPEN-closed.md |
| 75 | 🟢 | `sqx-worker.sh stop` sent right after `start` is lost | docs/OPEN-closed.md |
| 76 | 🟡 | Darwinex's real spread is 3–8× what `assets/` declares — the proposal is the... | OPEN.md |
| 77 | ⚪ | A one-item random group's hole can still drift to a different block | docs/OPEN-closed.md |
| 78 | 🟡 | MetaTrader 5 under Wine: built, not yet run | OPEN.md |
| 79 | 🟢 | SPP marginal profiles read θ₀'s lone level as argmax and spike | docs/OPEN-closed.md |
| 80 | 🟢 | Two studies read an old run with today's `_build.yaml` — runs should save the... | docs/OPEN-closed.md |
| 81 | 🟡 | The window's cut-over (plan 24) left five owner's calls open | OPEN.md |
| 82 | ⚪ | Crossmarket results of a retired project cannot be archived until the Family... | docs/OPEN-closed.md |
| 83 | 🟢 | The window cannot launch a second project on the custodian for 24 h after the... | docs/OPEN-closed.md |
| 84 | 🟡 | What the 2026-09-29 walk of the window left for the owner | OPEN.md |
| 85 | 🟠 | Prop-firm funding workstream — built 2026-09-29, the owner's calls still open | OPEN.md |

Read this index, then only the section you need: `grep -n '^## <N>' OPEN.md`.

## Notes

Provenance carried over from the old preamble, kept because it is not restated in any
issue body: this file was split out of `CLAUDE.md` on 2026-09-02, then migrated into the
rebuilt project tree on 2026-09-03 with its paths updated. The 2026-09-04 and 2026-09-21
review notes that used to sit here (issue 3 withdrawn, issues 6/7 resolved, the
three-install topology built and verified) are now folded into issues 3, 6, 7, 9 and 23
themselves — read those sections rather than this note.

---
## 19. 🟡 Three Monte Carlo thresholds are placeholders

`portfolio/common/monteCarlo/` ships with the thresholds the specification gave, and three of them are
not the owner's decision yet. Measured on the 36 strategies of `XAUUSD/Results` (2026-09-09):

1. **`scoring.survival_dd_pct` = 10% of the account.** Vetoes 21 of 36 on its own. It is a
   statement about **position size** as much as about the strategies — at 1,000 $ of risk on a
   100,000 $ account. It stays a placeholder until the prop-firm rules fix it.
2. **The dead-block veto** — any non-overlapping 24-month block with a negative bootstrap median —
   vetoes 30 of 36. The blocks are real losing periods, so the rule is doing work; but a rule that
   fails five of every six candidates is a threshold question. Alternatives in
   `portfolio/common/monteCarlo/POSSIBLE_IMPROVEMENTS.md` §1.
3. **The Family D sub-score saturates at 0** for every strategy, because it takes the worst of
   three parts and the worst block's 5th-percentile profit factor is almost always below 1. It is
   faithful to the specification and currently carries no information.

Nothing here is a bug and nothing blocks a run: the three live in `config.yaml` and `gates.py`, and
changing one re-decides every strategy without touching code.

**2026-09-29.** Owner, 2026-09-29: this is the trade-level Monte Carlo — deferred to the future. Not blocking.

---

## 22. 🟡 `studies/transfer/crossmarket` — state of play after the 2026-09-14/15 rebuild

Read `studies/transfer/crossmarket/README.md` first — it is now a folder map and an import-direction
table, not a file list — then the `README.md` of the layer you are touching (`inputs/`,
`mechanics/`, `model/`, `simulate/`, `verdict/`, `render/`, `explorer/`), then
`POSSIBLE_IMPROVEMENTS.md`. All of those are current as of the 2026-09-18/19 reorganisation into
layer packages, which moved 37 flat modules and changed no calculation. What is **not** written in
them:

**What changed, in one line each.** No verdict and no market is ever dropped (warnings replace the
gates). Nothing is cached or written to disk — the panel is the output. Random runs are priced in
dollars with the real trades' own sizes and costs, so net / DD / Ret/DD / Sharpe / PF are directly
comparable to SQX's. Four null models, 25,000 draws each per market. Test 1b (paired) and the market
drivers (PDF §5.4 metrics) are new. Everything runs on `envelope.window()` — the backtest's own span,
not the bar file's.

**Open threads, in the order they are worth picking up:**

1. 🔴 **The manual has no screenshots.** `docs/manual/07-otros-mercados-y-timeframes.pdf` (cap. 05-retest-mercados) describes every tab of a
   panel nobody has photographed. Rule 8 forbids inventing them; whoever next opens the panel for
   real should paste a few in. This is the only thing blocking that page from being finished.
2. 🟠 **Only 30 of the 757 strategies are exported.** `raw/XAUUSD/Retest_Markets_-_Family/2026-09-14`
   is a reproducible random sample (`--limit 30`, seed 20260914). The full export is one command and
   ~15 minutes on the worker.
3. 🟠 **`assets/_markets.yaml`'s `structural` category is empty**, so every conclusion so far rests on two
   correlated metals-and-energy markets. The edge-driver regression (`drivers.py` has the metrics,
   not the regression) needs six or more markets before it can be fitted at all, and the PCA on two
   markets is close to vacuous. This is the single change that would most improve what the module
   can say — and it is a retest the owner runs in the GUI, not code.
4. ⚪ **The shareable report was removed** (`text.py`, `panel.render`, the batch command) on the
   owner's instruction that the panel is a one-strategy tool. `reports/XAUUSD/Retest_Markets_-_Family/2026-09-14/crossmarket/`
   is an orphan left by the last batch run. Bringing the report back is a revert, not a rebuild, if
   he ever wants to send someone a page.
5. 🟠 **The only strictly unseen window of this project starts 2023-01-01, and nothing has been
   retested on it.** Added 2026-09-21, building the OOS-stretch tab. Every `dateTo` in every build
   and retest task stops at `2022.12.31` while the bar files run to 2026-01-16 (gold, silver) and
   2026-06-01 (Brent). So the 2018–2022 stretch the new tab tests is out of sample for the
   *generator* but not for the *project*: it entered selection through every `sampleType=127`
   acceptance condition and through the walk-forward matrix's OOS net profit, which is what the
   `selected_window` warning says. A retest over 2023-01-01 → today would be unseen for the base
   asset and for the additional markets at once, would need no such warning, and is a task the
   owner runs in the GUI. `knowhow/conditions/` holds the measurement.
7. ⚪ **`pending_fills` and `fill_mismatch` were measuring the wrong quantity — FIXED 2026-09-21.**
   `pending_fills` read the entry clock, `fill_mismatch` fired on any non-zero price error. Both now
   go through `mechanics/pricing.fill_profile()`: the entry **price** against its own bar's with the
   market's constant spread discounted, and the median error in ATR units against
   `diagnostics.max_fill_error`. Both verified to still fire (a feed displaced 3 ATR, 6% of entries
   moved half an ATR, H1 bars under an M30 backtest). On the three real markets both are now silent,
   which is correct: there are no intrabar fills in this fleet.
   `studies/transfer/crossmarket/POSSIBLE_IMPROVEMENTS.md` §4 holds every measurement.
8. ⚪ **M1 execution was considered for the random-entry study and is not needed by this fleet.**
   Asked 2026-09-21. It would fix nothing here: no strategy has a price exit, every exit lands on a
   bar open, the zero-duration trades share one timestamp (no interval exists at any resolution),
   and the 0.05–0.09 entry offset is a spread. Pricing on M1 would put the study on a grid SQX never
   executed on and *create* a mismatch. It becomes the right build the day a strategy carries a stop,
   a target or a trailing, and `mechanics/pricing.reconcile()`'s exit-side median error is the
   trigger to watch — 0.0000 on 757 of 757 today. Shape it would need then: entries drawn on the
   **logic** timeframe's grid (an M1 placement grid gives the null 30× more room and makes it a
   different, wider null), holds carried in minutes, pricing on M1.

**Two documented reversals live in `knowhow/research/hardest-null.md`** — a null's width is a measurement and
not an intuition, and a bar file is wider than the backtest that ran on it. Read them before
changing anything about how the nulls are placed.

**A gap in `tools/checks.py`, found 2026-09-15.** It verifies every `.py` appears in its folder
README, but not that every file the README names still exists — `text.py` sat in the table for a day
after being deleted. It also cannot catch a call-site broken by a signature change:
`sqx/export/export_bars.py` called `markets.feeds(asset)` for a day after that function started
taking a universe dict, and only failed at runtime. Both classes of drift are cheap to check.

**2026-09-29.** Owner, 2026-09-29: delete the 757 (the master XAUUSD project's `Retest Markets - Family` and `MC Trades`, 757 .sqx each, plus `AlgoData/raw|reports/XAUUSD/Retest_Markets_-_Family`). The master was closed; the deletion was refused by the session's safety classifier and waits on the owner running it or allowing it.

---

## 28. 🟠 `DAX40` has an asset file but the master configures no such feed

`assets/DAX40.yaml` names `DAX40_DukasM1_Infinox`, and a sweep of every `project.cfx` on the master
on 2026-09-22 found that symbol in none of them — the other sixteen assets all resolve. Its
`instrument` block and `sqx_now` values are therefore the ones read on 2026-09-03 and carried
forward, not re-read from the live install.

Either the feed was removed from the projects since, or the file was written for a market not yet
set up. **Not a finding against the master's configuration** — that is the owner's — just a note
that this one file cannot be refreshed from `sqx.inspect.instruments` until the feed exists.


---


## 29. 🟠 Six index assets have no IS/OOS window, and `SP500ft`'s feed does not exist

`assets/_policy.yaml` now carries `segments: <SYMBOL>:` for all seventeen, each with the date range
SQX actually holds for its feed (read 2026-09-22 with `-symbol action=list` on the conductor).
**Forex and metals were filled on 2026-09-22** — `build` 2008-01-01 to 2017-12-31, `oos1` to
2022-12-31, `oos2` to 2026-08-30, eleven assets. The **six index CFDs are still
`{from: null, to: null}`**: `window()` refuses to invent one and the preflight warns, so nothing
silently runs on a made-up window.

They were left out deliberately, and it is not a free choice — their histories start in 2011-2013,
so gold's 2008 build window would not fit and `validate()` would reject it:

| asset | data from | | asset | data from |
|---|---|---|---|---|
| EURUSD, GBPUSD, USDCHF, USDJPY, XAUUSD | 2003-05-05 | | NIKKEI225 | 2011-09-19 |
| AUDUSD, EURJPY, GBPJPY, USDCAD | 2003-08-04 | | USA500, USATEC | 2012-01-19 |
| AUDJPY | 2003-12-01 | | DAX40, DJ30 | 2013-09-30 |
| CADJPY | 2004-10-25 | | **SP500ft** | **none** |

⚠️ **`SP500ft_Plus02_Infinox` is in no SQX feed list**, so that asset cannot be built or tested at
all. Its `data` is null and `validate()` reports it. Either the feed needs setting up or the file
describes a market that was never wired.

**2026-09-29.** Also blocks index authoring (#35): no install defines a trading session for any index CFD, so `builder` refuses them until the session exists in SQX.

**2026-09-29.** Windows were already set (build → 2019, oos1 2020-2023, oos2 2024 → 2026-08-31) for the five index CFDs; `core.assets` passes for all five. Left for the owner, later: SP500ft's feed and the index sessions in SQX.

## 38b. 🟡 `/plugin` does not exist here — sqx-lab installed by hand, does not auto-update

**No narrative section was ever written for this issue** — it existed only as a status-table row in the old preamble, preserved here verbatim during the 2026-09-29 OPEN.md cleanup:

> new 2026-09-24: **`/plugin` no existe en este entorno**, así que `sqx-lab` va instalado a mano con `bin/sqx-lab-install.sh`. Funciona igual pero **no se actualiza solo**, y una versión nueva descomprimida encima se lleva la skill local `sqx-spp`. Hay que reejecutar el script tras cada actualización.

## 42. 🟡 Three Python entry points were never profiled, because they spend `oos2`

Encargo 18 (profiling the Python layer) closed on 2026-09-25 with commits `c9011a2` and
`3923010`: nulls, crossmarket, Monte Carlo, filters, CSCV, crossTF, variants, sppUltra, retest and
the gate's harvest, each measured before and after under `AlgoData/reports/perf-optim-2026-09-25`
and `AlgoData/profiling/bench-2026-09-25`, outputs identical. What it could not reach:
`walkForwardCorrelation/report.py` (step 17), its `pbo.py` path over `oos2` (step 18) and
`walkForwardMatrix/report.py` (step 19) — running them spends the reserved window, which is the
owner's one-way door. Measure them the first time the owner runs 17-19 for real, not before.
The MC Retest and the SPP were not measured at 500 either: their cost is SQX's (~34 h and ~2.8 h).

**2026-09-29.** Owner, 2026-09-29: measure 17-19 the first time they run for real; profiling them any earlier spends `oos2`. Waits on that run, not on code.

## 50. 🟡 Step 20 is built but decides nothing yet — three owner's calls, and 17-19 do not record themselves

`studies/closing/blindJoint/` (encargo 10 B, 2026-09-26) reads the four pieces and puts every
reading of "passes step 20" side by side; it cuts nobody until the owner chooses. Open, all his:
(1) `joint.pieces` × `joint.population` in its `config.yaml`; (2) `BlindJoint` in oos2's
`reserved_for` (`assets/_policy.yaml`) — without it the SPA on oos2 is never read; (3) the CSCV
reads oos2 and the policy does not list it. Engineering, not his: the WFC, CSCV and WFM reports
write no ledger row, so the blind door opens only after `python3 -m ledger.backfill --blind`
(`knowhow/eng/blind-steps-write-no-ledger-rows.md`); wiring them needs (3) first, or the CSCV's own
row would be refused. ⚠️ On 2026-09-26, exploring the USDJPY batches before the module existed,
the session read the two mothers' oos2 daily P&L (sums, correlation) outside the door; no ledger row
records that look — the owner decides whether to add one.

**2026-09-27 (encargo 24, E1):** (3) is decided — the owner put `CSCV` in oos2's `reserved_for`
(Q11). The WFC and the CSCV now write their own rows (one per segment read, through
`engines/variants/look.py`), and `ledger.blind` skips a batch that recorded itself. Still open: (1),
(2), the WFM (19) writing its own row, and `--family` — the WFC and the CSCV now require it and
`pipeline/recipe.yaml` and `ui/daemon/runner/optimisation.py` do not pass it yet (Q9 decides where
the family comes from).

**2026-09-28:** (2) is moot for a human — the owner lifted the oos2 reservation and the blind door
for humans (`knowhow/eng/oos2-door-binds-only-autonomous.md`), so the SPA on oos2 is read whenever a
human runs step 20. It stays open only for an autonomous agent (`ALGO_AUTONOMOUS=1`), together with
whether such an agent should be held at all.


## 76. 🟡 Darwinex's real spread is 3–8× what `assets/` declares — the proposal is the owner's to apply

`python3 -m studies.data.spread.scan` (2026-09-27), mean opening spread of Darwinex's ticks:
XAUUSD 9 → 63 points 2017 → 2026 against the declared 5 (build) / 10 (oos); USDJPY 4.7 → 10.4
points against 0.1. Neither is constant relative to price (owner's ±20 %: gold's worst year 1.96×,
USDJPY's 1.44×), so the study models the years before October 2017 and proposes, with the owner's
factor 1.25, a `%` commission per segment — XAUUSD 0.0131 / 0.0138 / 0.0118 % (build / oos1 /
oos2), USDJPY 0.0048 / 0.0052 / 0.0078 % — or 16 / 24 / 31 and 0.5 / 0.6 / 1.2 points.
`AlgoData/spread/<tick feed>/spread.html` has the table. **Applied 2026-09-27** to XAUUSD and the ten pairs too (`onboard --spread-only`: spreads, slippage = half, MC spread range; commission and swap kept). **Applied 2026-09-27 to the five index CFDs** on the owner's order: build data start–2019, oos1 2020–2023, oos2 2024–2026-08-31 with its own `spread_oos2` (the schema now allows a segment-named half), oos1/oos2 = Darwinex's mean daily spread in that segment × 1.25; build = the spread PROPORTIONAL to price (owner's option A, `model.fixed`) × 1.25, although fixed-points validates better; slippage = half; MC Retest spread range = the 2.5–97.5 % multiples of measured ÷ proportional mean, times the build spread. Their commission is still null and blocks authoring. Study: `docs/AgentPDFs/spread-real-2026-09-27.pdf`.

Three things are still open:
- **The repricing against SQX itself.** `studies.data.spread.report` swaps SQX's flat spread for
  the real one trade by trade (3 of 115 gold and 3 of 100 USDJPY strategies stop earning OOS). It
  has not been compared with a real DATATICK retest on `*_DarwTick_*` — one short worker job on
  a few strategies of an existing harvest licenses it as that retest's stand-in.
- **USDJPY's model leans on the price level** (`studies/data/spread/POSSIBLE_IMPROVEMENTS.md`):
  back in 2011–2012 it predicts the thinnest spreads of the history.
- **The «poquito de spread»** the owner keeps on top of the `%` is his to name.

**2026-09-29.** The spread study was applied (see above). Left: the owner's «poquito de spread» on top of the %, and whether to license the repricing with one short DATATICK retest on a worker.

**2026-09-29.** Owner, 2026-09-29: the «poquito de spread» is what `assets/` already carries — the measured spread × 1.25 as a spread on top of the commission (e.g. USDJPY 0.65 points + 8 $/lot). Left: the DATATICK retest that would license the repricing, and USDJPY's price-level model.

**2026-09-29.** Owner: make the DATATICK check part of the workflow, once, at the end. Now encargo 36 (`docs/encargos/36-licencia-reprecio-datatick.md`) and step 25.5 of `WORKFLOW.md`, after 17-20 and 25, before 26: a real `*_DarwTick_*` retest of a few survivors compared trade by trade with `studies.data.spread.report`. Left: the owner's acceptance bar (R difference or verdict match), and building it.

## 78. 🟡 MetaTrader 5 under Wine: built, not yet run

2026-09-27, owner: test the surviving strategies in MT5 before the portfolio, and give Claude an MCP
over the terminal — backtest, compare with SQX, read-only data; **no order tools**. Built: `mt5/`
(`server.py` registered in `.mcp.json`), `bin/mt5-wine-system.sh` (the root half of MetaQuotes'
official `mt5linux.sh`, without its `apt upgrade`) and `bin/mt5-install.sh` (prefix at `mt5_prefix`,
generic MetaQuotes terminal, Windows Python 3.12 + `MetaTrader5==5.0.6231`). Manual `60-mt5.md`.

Remains, in order:
1. The owner runs `bin/mt5-wine-system.sh` (sudo); then `bin/mt5-install.sh` and the demo login by hand.
2. Verify against a real terminal what was written from the MT5 docs, unrun: the tester ini keys, the
   report's deal rows (13 cells, English `in`/`out`/`buy`/`sell` — a terminal in another language may
   write them translated), `origin.txt` naming the install, MetaEditor compiling a whole folder.
3. The `.mq5`: `sqcli -h` has no verb for it (checked 2026-09-29). Next: a `Test_` project with a
   SaveToFiles task, `SaveSourceCode` + `MNActive` (`knowhow/sqx-drive/export-mql5-source-headless.md`);
   the MT5 generator's name is still to find.
4. The owner sets the bar for "the EA reproduces SQX" (`matched_of_sqx`, gaps) on the first real strategy.

**2026-09-29.** Wine 11.18 staging (owner, sudo), terminal build 6231, the owner's funded account
(Hantec, hedging, `trade_mode` real, symbols suffixed `.h`, terminal in English). `mt5/live.py` reads
account, symbols, bars — verified. Build 6231 ships **MetaQuotes' own MCP** (67 tools, 127.0.0.1:22346,
Bearer token): registered at **local** scope as `metatrader5` (token in `~/.claude.json`, never in git);
its six `trade_*`, `chart_add_expert` and `chart_add_script` are **denied** in `.claude/settings.json`
(owner's choice). Its tester (`tester_prepare_config` → `tester_run_backtest` → `tester_get_report` json)
runs with the terminal open, so it replaces `mt5/tester.py` + `mt5/report.py` **once a real run shows
its report carries every deal**; until then they stay. It has no compile tool: `mt5/metaeditor.py`
stays. `mt5/compare.py` and the Parquet exports stay — MetaQuotes' MCP has neither.
**Planned (owner, 2026-09-29), not built:** multi-account backtests from the one terminal
(Hantec, FTMO; `mt5.login` with the saved password per job, symbol map per account, window and
model chosen per request because some prop firms' data is poor — a per-account data probe first),
then **`weeklyReconciler`**: each weekend, SQX backtests of the live strategies over the last week on
the development data, against the live trades (live EAs run on a separate server; this machine
reads, investor password recommended); a report, form to be decided. Cron slot after
`weekly-data-update` (Sat 03:00).
Note: `Bash(*)` is allowed in this project, so the deny list stops the MCP tools, not a hand-made
HTTP call to the port — the terminal's own "prohibit AI trading" option is the lock that holds.

**2026-09-29.** Install and login DONE: the terminal runs under Wine (`~/Desktop/MT5`), connected, logged in to «$10k FTMO Account 2-Step» on FTMO-Server4 (owner: several funded accounts). Left, all ours: `metaeditor` is not installed (needed by `mt5_compile`), then backtest one SQX EA in the tester and compare it with SQX.

**2026-09-29.** Compile works: `MetaEditor64.exe` was there (case bug in `mt5/wine.py`); Wine truncates any argument with a space, so `compile_path` now compiles by a relative path with `cwd`, and refuses while the terminal is up (they share the data-folder lock). 48/48 `Sq*` indicators compiled, 0 errors. Left: (1) no SQX-exported EA exists on disk — export one through a `Test_` project's SaveToFiles task (`SaveSourceCode`) on the conductor; (2) the tester and MetaEditor need the terminal closed, and it runs logged in to the owner's funded FTMO account — his call when. Proposed bar: matched ≥ 95 % both ways, open gap ≤ 1 bar, same exit ≥ 90 %, P&L corr ≥ 0.95. `knowhow/eng/metaeditor-compile-under-wine.md`.

**2026-09-29.** Owner, 2026-09-29: MT5 is on hold until he says so — do not touch the terminal, the tester or MetaEditor meanwhile.

**2026-09-29, later — owner lifted the hold for this test.** The unattended backtest works: `metaeditor.expert()` → `tester.start()` → `tester.collect()` on the owner's `Strategy 3.48.75` (XAUUSD H1, `~/Desktop/FTMO_EAs_NoNews` and `FTMONewsFilter_Files`), 20 months in ~15 s each, 27 trades parsed from the report. One bug fixed: the terminal does not create the `reports\` folder of `Report=`, so no report was written (`tester.py` makes it now). The news filter is inert in the tester (the calendar is empty there), so both versions trade identically. → `knowhow/eng/mt5-tester-unattended.md`. Left: the tester has no way to pass EA inputs (a `[TesterInputs]` section); the MetaQuotes MCP tester is still unproven; there is still no SQX backtest of the same EA to compare against.

## 81. 🟡 The window's cut-over (plan 24) left five owner's calls open

2026-09-28, closing F13 of `docs/encargos/24-plan-ventana.md` — the owner: «borra la UI anterior;
quiero que en esta máquina esté solo la nueva». The waves ran without gates at the
owner's instruction («programa TODO lo que falte… borra la UI anterior»); where a question was
still open the plan applied its recommended reading (§10) and the owner corrects afterwards. These
five are his, and nothing in the code decides them:

1. **The three ledger files of USDJPY.** Plan 24 §10 says every front left them untouched,
   «decisión del dueño pendiente», without naming them. On disk the likely three are the
   harnesses' — `AlgoData/ledger/USDJPY_H1_perf.jsonl`, `USDJPY_H1_TestUSDJPY_Workflow_v1.jsonl`,
   `USDJPY_H1_USDJPY_workflow_profiling_v1.jsonl` (the last one's project was retired on
   2026-09-27; F13 only stopped the tests using it) — beside the two of the Donchian study. Keep, archive or delete: his call; they count
   searches in Registro de búsquedas meanwhile.
2. **«Subprueba del MC Retest».** F5's acceptance asked to re-run «one MC Retest sub-test»; what it
   built and tested re-runs one test of the trade-level Monte Carlo (`monteCarlo`, by its title)
   or one crossmarket market, beside the stored result (`knowhow/eng/partial-reruns-beside-stored.md`).
   Whether the owner meant that, or one of the eight SQX MC Retest perturbation tasks (an SQX run,
   not a Python one), is his to say.
3. **The default step when archiving.** «Archivar» (F4) asks the step with no default, because the
   rail's last «hecho» can be a reading past a sealed 17-19. Keep it without a default, or name
   the rule.
4. **The knobs chosen for the window.** Q4 (a check in `tools/checks.py`, the rail stays in code),
   Q5 (show «0» where Min Distance is `null`, the YAML untouched), Q15 (filters AND only) and Q17
   (Configuración SQX writes `_build.yaml` for new projects) were applied as recommended.
5. **F7's live test.** «Continuar workflow» is built and tested with every SQX call faked
   (`tests/test_advance.py`, `test_advance_edges.py`); the live run on the conductor with
   `Test_UiContinuar_USDJPY` (Q20) waits for the owner (plan 24 §6).

**2026-09-29.** Item 1 done (owner): the three harness ledgers `USDJPY_H1_perf`, `USDJPY_H1_TestUSDJPY_Workflow_v1`, `USDJPY_H1_USDJPY_workflow_profiling_v1` moved to `AlgoData/ledger/archive/`; the Donchian study's two stay. Items 2-5 still open.

## 84. 🟡 What the 2026-09-29 walk of the window left for the owner

🔬 2026-09-29, every button of the window driven on `Test_USDJPY_donchianUpperCrossUp_M30` (steps
13-20 from the rail). The window's bugs found were fixed; these are the owner's calls:

- **A retest that does not empty its output leaves two populations in it.** `OOS`, `MCR 1 Bar`,
  `MCR 2 Spread` and `WFM` of that project hold today's strategies beside earlier ones (saved as
  «Strategy X(1)»), and the harvest pairs by name, so it read the older copies. No `Clear
  databanks` task exists in the project. The launch confirmations now warn; whether the workflow
  project should clear an output before its task is a project-configuration decision.
- **`MCR 3 Slippage` moved nothing on USDJPY** — 1,000 identical simulations for all 21
  strategies (`tarea_sin_dispersion`): 0.325-1.3 points of slippage do not change a market-entry
  M30 strategy. The range (`assets/_policy.yaml`) is his.
- **Steps 10.5 and 16.5 have no button** (the /crosstf and /variants fabrication: the mothers
  to pick and a clamped/rounding review), so 11, 16.5-18.5 cannot be run from the window.
- **Estrategia needs ~1,480 px of width**: it fits 1920, not 1280. A redesign, not a fix.
- **The interview asks «transición o estado» after a sentence that says «cruza»** — it could
  infer it; left as it is.
- During the WFM SQX logs thousands of `StatsComputer - Exception computing databank column
  ParameterCount / DoFRatio` (SQX's own, harmless to the run; the watcher now ignores them).

**2026-09-29.** Owner, 2026-09-29: MCR 3's slippage stays at half the spread, his rule — `tarea_sin_dispersion` on USDJPY is an honest reading, not a range to widen. Still open: whether the workflow project clears an output before its task.

**2026-09-29.** Owner, 2026-09-29: our tool never clears a databank before a retest — «en SQX se puede considerar, en nuestra herramienta ni de coña». The launch warning stays. Still open: the missing buttons for 10.5 and 16.5, Estrategia's width, the interview inference.

## 85. 🟠 Prop-firm funding workstream — built 2026-09-29, the owner's calls still open

📓 2026-09-29, one session with the owner. Everything below exists; this section keeps what is open
so it is not lost.

**Built.** The catalogue database `AlgoData/funding/funding.sqlite` (`portfolio/funded/catalog/`,
every plan, rule and add-on combination priced, with history; CSV copies in `AlgoData/funding/csv/`),
refreshed Sundays 06:30 by the `fundingWatcher` agent. Offers: `portfolio/funded/deals/`, daily
10:00 by the `dealHunter` agent, desktop notification, `python3 -m portfolio.funded.deals.worth`.
The firm register `AlgoData/funding/firms.yaml` and the `/firm-onboard` protocol. Encargo 33 (the
economics: bank cash flow, EV per plan), encargo 34 (step 26: MT5 validation on each firm's feed →
validated pool). Manual chapters 73 and 74.

**Decided by the owner, 2026-09-29** (written in the encargos; do not re-ask):
- Prices are list prices; discounts live only in `deals`.
- First iteration: accounts of **10k USD at most**, EAs allowed, **active firms only**.
- Steps 1-25 use `oos2` first; then step 26 (MT5 on the firm's feed) and only its validated pool
  reaches the portfolio. Step 26's thresholds are input parameters, his proposed values accepted.
- Risk shape from the long SQX history translated to each firm; edge level from OOS with haircut `h`.
- Only the owner makes a firm active. A deal notifies only if it beats the best known price.

**Open — the owner's calls:**
1. **Cash budget**: the most he will spend on challenges before a first payout (encargo 33 §3.5).
2. **FundedNext** (candidate): the EA usage fee's amount; accepting one account per portfolio
   (identical trades across accounts are banned); gates G3 Spain and G4 payout record; then activate
   or not — `docs/AgentPDFs/fondeo-admision-fundednext-2026-09-29.md`.
3. **FundingPips** (candidate, blocked): may a self-built SQX EA trade? Ask its support. If yes,
   confirm the 8 typed prices and rules in the universe (`AlgoData/funding/manual/fundingpips.yaml`,
   `confirmed: false`) — `docs/AgentPDFs/fondeo-admision-fundingpips-2026-09-29.md`.
4. **FTMO**: is the 2-Step fee refund per account? Read as yes, unconfirmed — ask support
   (`rules/ftmo.yaml`, `fee_refund_scope`).
5. **Hantec**: whether the fee is refunded; whether the "Profit Target −2 %" add-on lowers every
   phase or only phase 1; its prohibited-strategies article (the watcher has not found it).
6. `portfolio/DECISIONS.md` #11, the remainder: with `oos2` spent, what validates the chosen
   combination (the firm-feed period, a live incubation, nothing).
7. The rest of encargo 33 §6 (risk per phase, re-buy policy, which `h` to show).

**Open — to verify:** the news filter of `mt5/newsfilter` (`/ea-news`, 2026-09-29) compiles and
sits where the hand FTMO patch did, but its live behaviour is unseen — the tester has no calendar. Put a
`_Hantec` EA on a demo chart across one red-folder release and read the Experts tab for the close line.

**Open — to build:** encargo 33 (the EV model, then plug it into `deals.worth`, which today judges a
deal only by the zero-edge floor); encargo 34 (waits on #78); a test of Hantec's price formula
against its page's JS.

**Known limits:** the notification only shows if the desktop session is up at 10:00 (the deal stays
in the table); FundingPips' catalogue is typed and unconfirmed because its site blocks automated
reading, which is not forced; codes of firms without a public check stay `unverified`.

## Constraints discovered while investigating

- **SQX rewrites every `project.cfx` on save/exit.** All 14 project files were restamped within the
  same second (`14:33:43`, 2026-09-02). Editing a `project.cfx` on disk while the GUI holds that
  project **will be silently overwritten**. Config edits must be made in the GUI, or on disk only
  while SQX is not running.
- `project.cfx` is a plain ZIP: `config.xml` + one `<Type>-Task<N>.xml` per task. Safe to *read*
  at any time.

