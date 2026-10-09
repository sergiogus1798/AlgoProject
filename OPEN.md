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
| 28 | 🟠 | `DAX40`'s feed is in SQX's registry but in no project — builds, not yet run | OPEN.md |
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
| 76 | ⚪ | Darwinex's real spread is 3–8× what `assets/` declares — the proposal is the... | docs/OPEN-closed.md |
| 77 | ⚪ | A one-item random group's hole can still drift to a different block | docs/OPEN-closed.md |
| 78 | 🟡 | MetaTrader 5 under Wine: built, not yet run | OPEN.md |
| 79 | 🟢 | SPP marginal profiles read θ₀'s lone level as argmax and spike | docs/OPEN-closed.md |
| 80 | 🟢 | Two studies read an old run with today's `_build.yaml` — runs should save the... | docs/OPEN-closed.md |
| 81 | 🟡 | The window's cut-over (plan 24) left five owner's calls open | OPEN.md |
| 82 | ⚪ | Crossmarket results of a retired project cannot be archived until the Family... | docs/OPEN-closed.md |
| 83 | 🟢 | The window cannot launch a second project on the custodian for 24 h after the... | docs/OPEN-closed.md |
| 84 | 🟡 | What the 2026-09-29 walk of the window left for the owner | OPEN.md |
| 85 | 🟠 | Prop-firm funding workstream — built 2026-09-29, the owner's calls still open | OPEN.md |
| 86 | 🟡 | Audit 2026-09-30: exports without manifest, a `migrate` code_version, two files over 250 lines | OPEN.md |
| 87 | 🟠 | Portfolio construction engine — M0-M2, F1 and the F2 engine built 2026-09-30; the owner's calls gate each milestone | OPEN.md |
| 88 | 🟠 | SQX's daily curve is each day's LOW equity, not a mark to market — readers that difference it | OPEN.md |
| 89 | 🟡 | What the 2026-09-30 H1 workflow run (steps 5-26) left open | OPEN.md |
| 90 | 🟡 | The autopilot — phase 1 ran end to end 2026-10-01, its holes fixed | OPEN.md |
| 91 | 🟠 | The gate's t was compressed (fixed 2026-10-02); every threshold and null FPR read on the old scale is stale | OPEN.md |
| 92 | 🟢 | Data root over budget: `reports` 5.05 GB > 5 GB (audit 2026-10-02) | docs/OPEN-closed.md |
| 93 | 🔴 | Criteria of steps 6 and 8 proposed 2026-10-02 — four owner decisions, 15 assets unmeasured | OPEN.md |
| 94 | 🟢 | `ledger/thresholds.py` splits the feed name `UKOIL.cash_M1` on its dot — `ledger.report --check-thresholds` crashes | docs/OPEN-closed.md |
| 95 | 🟡 | Twelve tests set aside in `tools/audit_tests.py` — each with its reason, so the skip list has an owner | OPEN.md |
| 96 | 🟡 | `core.surface.trials.independent` over-counts when one family holds more than half (rule kept, owner 2026-10-02); the raw crash is now a clear error | OPEN.md |
| 97 | 🟢 | `core.sqxfile.symbol()` returns ("", "") for a symbol with a dot, a lowercase letter or an `@` | docs/OPEN-closed.md |
| 98 | 🟢 | Nothing reads SQX's own `StrategyProblems` flag | docs/OPEN-closed.md |
| 99 | 🟢 | `mt5.tester.collect()` ignores the tester's history quality and its «start time changed» line | docs/OPEN-closed.md |
| 100 | 🟠 | Literature scout built 2026-10-02 — owner decisions pending, 8 questions and 8 entries without a condition | OPEN.md |
| 101 | 🟢 | A proposal's stamp counts its own three ideas as already spent — «ya van 3 ideas», rank 311 instead of 1 | docs/OPEN-closed.md |
| 102 | 🟠 | Knowhow cards filed in the wrong domain (weekly quality pass 2026-10-04) — to move or leave, owner's call | OPEN.md |
| 103 | 🟢 | `python3 -m sqx.inspect.instruments` crashes (empty `commissions` attribute) — the asset-override check cannot run | docs/OPEN-closed.md |
| 104 | 🟡 | Portfolio build 2026-10-05: six findings left unfixed (universe cache, frozen version, GA rank saturation, `funded_b` overwrite, pyarrow abort, `test_portfolio_build`) | OPEN.md |
| 105 | 🟢 | `execute.synced` divides by `poll_seconds`: 0 raises ZeroDivisionError instead of SystemExit | docs/OPEN-closed.md |
| 106 | 🟢 | Leftovers of the September infra and calculation reviews (reports deleted 2026-10-06): one spread suspicion (m30), five small infra items | docs/OPEN-closed.md |
| 107 | 🟡 | Seven tests fail in the 2026-10-07 mechanical audit: four depend on data deleted by the 10-06 disk cleanup, one on cwd (`afterrun` stop path), two undiagnosed | OPEN.md |
| 108 | 🟠 | Step 12 redesigned (T0-T4, steps 11.5 and 11.7) built beside the old one: waits for the first real run and the owner's «corta» | OPEN.md |
| 109 | 🟠 | mcRetest «Estrategia a estrategia» table fails to draw in the window: 11 help entries for 8 columns | OPEN.md |

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

**2026-10-06.** The owner's 2026-09-29 decision is carried out on the data root: `raw|reports|metrics/XAUUSD/Retest_Markets_-_Family` and `raw|metrics/XAUUSD/MC_Trades` deleted (36 MB; no code read them). The 757 `.sqx` inside the master's XAUUSD project stay his to delete.

**2026-10-07.** The study this section describes was replaced by encargo 46 (2026-10-07): step 10 now asks «does the logic travel?» through nine facts P1-P9 read from one joint tensor of year-shifted random runs (studies/transfer/crossmarket/travel/, judged on gross R), and the old nulls-per-market, breadth, Fieller, Timing Alpha, exposure and window-sweep code (simulate/, verdict/, mechanics/, orchestrate/, six contract/ files) was deleted. The state of play below is history; what is left open is the calibration of the P1-P9 lines (criteria.yaml, PROVISIONAL).

---

## 28. 🟠 `DAX40`'s feed is in SQX's registry but in no project — builds, not yet run

Stale until 2026-10-02: this said the master had no DAX40 feed and named `DAX40_DukasM1_Infinox`.
Today the master's Data Manager holds `DAX40_M1` (instrument `DAX40_ftmo`, FTMO, EETUS, 3.9 M bars
from 2013-09-30) and `DAX40_TICK` (from 2018-06), with bars under `user/data/History/`; the card
names `DAX40_M1` and `python3 -m core.assets DAX40` exits 0. What is still true: **no `project.cfx`
on any install carries that feed**, so the builder writes its resources from the registry
(`registryxml.definitions`, `knowhow/costs/sessions-live-in-data-db.md`). A DAX40 H1 project built
into a temp install carries main chart `DAX40_M1`, instrument `DAX40_ftmo`, session
`GER40.cash_ftmo`. **Open: nobody has started such a project in SQX yet** — the first real run is
the proof that SQX resolves it; on USA500 the registry route and the project route give
byte-identical tasks.


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

**2026-10-04.** The index windows are filled since 2026-10-01 (assets/_policy.yaml: UKOIL, DAX40, DJ30 and the rest carry build/oos1/oos2). What is left is only SP500ft, whose feed does not exist in SQX (data: null), and the index sessions.

## 38b. 🟡 `/plugin` does not exist here — sqx-lab installed by hand, does not auto-update

**No narrative section was ever written for this issue** — it existed only as a status-table row in the old preamble, preserved here verbatim during the 2026-09-29 OPEN.md cleanup:

> new 2026-09-24: **`/plugin` no existe en este entorno**, así que `sqx-lab` va instalado a mano con `bin/sqx-lab-install.sh`. Funciona igual pero **no se actualiza solo**, y una versión nueva descomprimida encima se lleva la skill local `sqx-spp`. Hay que reejecutar el script tras cada actualización.

**2026-10-04.** bin/sqx-lab-install.sh wires only sqx-custom-block, sqx-random-group and sqx-strategy-template and retires the sqx-spp and sqx-strategy-project links, so a vendor update no longer shadows /spp. The only step left is re-running that script by hand after each update.

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
(`knowhow/pipeline/blind-steps-write-no-ledger-rows.md`); wiring them needs (3) first, or the CSCV's own
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
for humans (`knowhow/pipeline/oos2-door-binds-only-autonomous.md`), so the SPA on oos2 is read whenever a
human runs step 20. It stays open only for an autonomous agent (`ALGO_AUTONOMOUS=1`), together with
whether such an agent should be held at all.

**2026-10-04.** Done since this was written: joint.population is decided (entrantes, studies/closing/blindJoint/config.yaml), the WFM writes its own ledger row (studies/optimisation/wfm/report.py calls steprows.log_wfm) and CSCV and WFM are in oos2's reserved_for (assets/_policy.yaml). Still the owner's: joint.pieces is null, so step 20 cuts nobody, and whether an autonomous agent is held out of oos2 for BlindJoint.

**2026-10-04.** Owner, 2026-10-04: joint.pieces = sin_fallo (studies/closing/blindJoint/config.yaml); with population = entrantes step 20 now makes one reading the call. tests/test_blindjoint.py updated and passing. Still open: whether an autonomous agent is held out of oos2 for BlindJoint (not in reserved_for).

**2026-10-07.** Encargo 48 (steps 16.5 and 17 rebuilt, 2026-10-07), part V still open: a real variant batch with `variant_trades.parquet` has never been produced, so the real read in `studies/optimisation/wfc/inputs/batch.py`, the export in `pipeline/autopilot/variants.py` (`export_retest --batch variants` + `sqx.variants.varianttrades`), the build -> oos1 rehearsal of `studies.optimisation.wfc.calibrate` (probed only on a synthetic batch) and the window's two zones (WFC and parameter cloud) are unverified against real data. The owner then put a sign-flip null on the level (PASA needs the top median > 0 and its p <= 0.05; a top that wins without beating the null is LIMBO), and the recalibration wrote `abre: true` (false PASA with no edge 0.02 under the 0.40 cap, false NO PASA at Sharpe 0.5 0.22 under 0.25; `AlgoData/ledger/wfc_calibration.md`), so `ledger.gate.seal` now lets step 17 read oos2: the first read must be the real blind block, never a test. Step 20 now translates the state (PASA = no failure, NO PASA = failure, LIMBO = undecided); the old ledger-row wiring problem above is superseded for the WFC, which writes one row per segment via `engines/variants/look.py`.

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
`weekly-data-update` (Sat 02:00). **2026-09-30:** it shares its retest of the fresh stretch with the
portfolio's paper OOS (`portfolio/PLAN.md` §14.5 M9 — one retest, two readers), and the floating
rebuild of §14.2 lets it reconcile live MAE, not only P&L.
Note: `Bash(*)` is allowed in this project, so the deny list stops the MCP tools, not a hand-made
HTTP call to the port — the terminal's own "prohibit AI trading" option is the lock that holds.

**2026-09-29.** Install and login DONE: the terminal runs under Wine (`~/Desktop/MT5`), connected, logged in to «$10k FTMO Account 2-Step» on FTMO-Server4 (owner: several funded accounts). Left, all ours: `metaeditor` is not installed (needed by `mt5_compile`), then backtest one SQX EA in the tester and compare it with SQX.

**2026-09-29.** Compile works: `MetaEditor64.exe` was there (case bug in `mt5/wine.py`); Wine truncates any argument with a space, so `compile_path` now compiles by a relative path with `cwd`, and refuses while the terminal is up (they share the data-folder lock). 48/48 `Sq*` indicators compiled, 0 errors. Left: (1) no SQX-exported EA exists on disk — export one through a `Test_` project's SaveToFiles task (`SaveSourceCode`) on the conductor; (2) the tester and MetaEditor need the terminal closed, and it runs logged in to the owner's funded FTMO account — his call when. Proposed bar: matched ≥ 95 % both ways, open gap ≤ 1 bar, same exit ≥ 90 %, P&L corr ≥ 0.95. `knowhow/mt5/metaeditor-compile-under-wine.md`.

**2026-09-29.** Owner, 2026-09-29: MT5 is on hold until he says so — do not touch the terminal, the tester or MetaEditor meanwhile.

**2026-09-29, later — owner lifted the hold for this test.** The unattended backtest works: `metaeditor.expert()` → `tester.start()` → `tester.collect()` on the owner's `Strategy 3.48.75` (XAUUSD H1, `~/Desktop/FTMO_EAs_NoNews` and `FTMONewsFilter_Files`), 20 months in ~15 s each, 27 trades parsed from the report. One bug fixed: the terminal does not create the `reports\` folder of `Report=`, so no report was written (`tester.py` makes it now). The news filter is inert in the tester (the calendar is empty there), so both versions trade identically. → `knowhow/mt5/mt5-tester-unattended.md`. Left: the tester has no way to pass EA inputs (a `[TesterInputs]` section); the MetaQuotes MCP tester is still unproven; there is still no SQX backtest of the same EA to compare against.

**2026-09-29, evening — MT5 Bridge › Verificar built (encargo 34 §0.5).** Point 3 is solved: a
SaveToFiles task with `<SaveSourceCode type="Expert Advisor for MetaTrader5 (*.MQ5)">` exports the
EA headless (the GUI's label «MetaTrader 5 (*.mq5)» fails the project;
`knowhow/sqx-drive/export-mql5-source-headless.md`). The terminal switches between the owner's
saved FTMO and Hantec accounts on its own — `initialize(login, server)` with the terminal started
detached first, and a `[Common] Login/Server` section in the tester ini
(`knowhow/mt5/mt5-account-switch-unattended.md`). `python3 -m mt5.verify.run` and the window's
new MT5 BRIDGE section run the whole check. Still open from this section: point 4 is now the
owner's thresholds of encargo 34 (in `ledger/thresholds.yaml`, `mt5verify.*`); the MetaQuotes MCP
tester stays unproven; the tester still cannot pass EA inputs.

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
- **2026-09-30, delegated to the session** (`portfolio/DECISIONS.md` #13): the funded portfolio is
  chosen by the engine with the funded yardstick — P(pass) of one plan on `build`, from intraday
  floating equity (MAE and MFE) on the firm's server day — and judged on `oos1`+`oos2`; encargo 33
  keeps the rules (moved up, the engine calls them) and the bank simulation, and no longer chooses the
  portfolio. Funded path first (owner's priority). → `portfolio/PLAN.md` §14.

**Open — the owner's calls:**
1. ~~**Cash budget**~~ — **answered 2026-09-29: 1,000 € in total** (encargo 33 §3.5; plans are in
   USD, converted at the day's rate).
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
2026-10-02 (encargo 42): the tester mode exists — the patched EA reads the firm's history from
Common\Files and was seen to close 5 min before and to refuse entries on three hand-checked releases
(`knowhow/mt5/ea-news-filter.md`). Still open: the live close on a demo chart; the EAs in
`AlgoData/mt5/eas/` were regenerated 2026-10-02 in AlgoData only (backup in `eas-backup-2026-10-02/`) — `Experts/` and
the live charts still carry the old ones; the thin-day exclusion and the no-minute events' removal are not yet seen in a tester run; the first real
with/without reading waits for the owner's strategy and firm; FTMO-Server4 lacks USDJPY M1 for
2023-09-20→2023-11-10 (`knowhow/mt5/mt5-tester-m1-gaps-hide-news-window.md`).

**Open — to build:** encargo 33 (the EV model, then plug it into `deals.worth`, which today judges a
deal only by the zero-edge floor); encargo 34's pool (its verification is built, 2026-09-29: MT5
BRIDGE › Verificar, §0.5 of the encargo, with its open points); a test of Hantec's price formula
against its page's JS. Hantec's commission on gold is unconfirmed, so the verification refuses
Hantec on XAUUSD until it is filled in the Activos zone.

**Known limits:** the notification only shows if the desktop session is up at 10:00 (the deal stays
in the table); FundingPips' catalogue is typed and unconfirmed because its site blocks automated
reading, which is not forced; codes of firms without a public check stay `unverified`.

**2026-10-04.** Council decision 2026-10-04 (F1-F4): FTMO 2-Step fee refund modelled as NO refund per account (rules/ftmo.yaml fee_refund=false, unconfirmed; cost per 1,000 USD of passed account 20.0 -> 30.0 on the 10k plan); Hantec add-on Profit Target -2 % lowers phase 1 only (combos.EFFECTS, moves no number: sold on Express only), Hantec no fee refund, rejected on XAUUSD as today; FundedNext stays candidate, FundingPips blocked. Owner sends the three support messages: scratchpad support_questions.md (c2 session).

**2026-10-05.** 2026-10-05 build of the funding economics (portfolio PLAN §9 F2-F5, impl log phases 2-4): the owner answered encargo 33 §6.4 (re-buy: both policies compared, a searched dimension) and §6.7 (haircuts [0, 0.25, 0.5, 0.75, 1], 0.5 decides), plus R5 (open-risk cap per plan), F3 `stageb.shared_of: larger`, F4 `verdict.pass_measure: mc_p`. F2-F5, `funded/decide/` and `deals.worth` are built with known-answer tests and ran on the relaxed `Test_nikkei_ref` pool under the TEST root only (chapters 88, 102): NOTHING real has been run — no real pool, no real-root bank table, no oos2 read. Still `null` and refusing: `funded.open_risk_cap`, `stageb.t1_gap`, `verdict.pass_percentile` (unset = no funded portfolio can pass, decide always says «ninguno»), `owner.eurusd`, `payout_cushion`, `tax_rate`, `payout_fee`, `p_payout_denied`, `p_firm_closes_year`, `gaps.hantec_endurance_payout_days`, `gaps.hantec_express_floor_after_payout`, `gaps.ftmo_1step_floor_after_payout`; also the bank horizon and edge source (CLI-required). Findings left unfixed: #104. Open until a real pool runs.

## 88. 🟠 SQX's daily curve is each day's LOW equity, not a mark to market — readers that difference it
🔬 2026-09-30, portfolio engine wave 1: `dailyEquity.bin` (and every `equity.parquet` built from it)
holds, per trading day on the feed's clock, the day's **lowest** equity — closed P&L plus open
positions at their worst M1 wick. The M1 rebuild matches it on 100 % of 3,983 days of the archived
USDJPY strategy (max 0.16 $); the MTM close matches 45 %. → `knowhow/sqx-format/daily-equity-bin.md`,
golden `tests/test_portfolio_universe.py`.
- **Affected, not changed (other workstreams):** anything that differences this curve as daily
  P&L — the variant batches' `equity.parquet` read by the WFC and the CSCV (`engines/variants/`),
  `studies/screening/snoopingScreen/`, `studies/closing/blindJoint/`, `studies/closing/exposure/`.
  Their totals are right (the differences telescope); their day-by-day values, Sharpe and
  correlations are low-to-low. Decide per study whether it matters; a daily MTM series needs trades
  + M1 (`portfolio/common/construct/equity/`).
- The portfolio engine already uses the curve only as a known answer, never as P&L.

**2026-10-04.** 2026-10-04 point 1.5 measured on three populations (60 / 3,786 / 3,732 strategies, oos1): snoopingScreen benchmark 15-26 % oversized, SPA p 0.72→0.58 / 0.95→0.95 / 0.79→0.73, StepM names 0 either way, rebuild recommended (≈1 s CPU per strategy); blindJoint same engine, not measured; CSCV PBO 0.37→0.35, 0.36→0.39, 0.40→0.52, rebuild needs trades per variant (SQX export at step 16.5); decay t = 0.78-0.88× close-based, order unchanged, use drift_excess_t instead; WFC does not read the curve and exposure/worst_day_r are 0.97-1.00× — WFC and exposure can come off the affected-readers list (exposure: document only). Also: the rebuild in construct/equity/paths.py does not reconcile on USDJPY (0 of 3,732 within 1 $; USA500 97 %); gap in the one strategy opened = 5 $/lot commission while a position is open (cause inferred). Waiting on the owner: harvest trades per variant at 16.5 for the CSCV? Cards: knowhow/sqx-format/daily-equity-bin.md, equity-reconstruction-usdjpy-gap.md; tables AlgoData/scratch/null-fpr-2026-10-04/.

**2026-10-04.** The USDJPY gap of the reconstruction is explained and fixed: SQX takes the whole round-turn commission off the floating equity from the entry, the rebuild booked it at the close (gap / lots = 5.000 $, R² 1.0000 over 182,389 strategy-days). `paths.minute_path` takes a `commission` argument; USDJPY reconciles 3,729 of 3,732 (was 0), USA500 unchanged at 97.3 %. snoopingScreen now reads the close-to-close curve (`equity/closecurve.py`); blindJoint has the same code but refuses its SPA until step 16.5 harvests `trades.parquet` per variant. Still owed: `search/stageb_data.py:62` calls `minute_path` without the commission, universe caches built before today must be rebuilt, the PercentageBased branch is unverified, and a perf target for `closecurve`.

## 91. 🟠 The gate's t was compressed (fixed 2026-10-02); every threshold and null FPR read on the old scale is stale
🔬 `studies/screening/analysis/decay.py` put the annualised Sharpe inside Lo's variance term: `t`
was compressed and capped at √(2·years). Fixed; old 1.3 / 1.65 / 2.0 = new 1.42 / 1.92 / 2.55 on a
5-year oos1. The gate also gained `trade_t`, `drift_excess_t` and the floating-risk columns in R,
for every paired strategy. → `knowhow/research/gate-t-scales.md`, `studies/screening/gate/README.md`.
- **Nothing in `ledger/thresholds.yaml` moved, and no gate threshold reads the t** (`degradacion.min_t`
  is 0.0 in `config.yaml`: a sign test, scale-free). What reads the new scale today: the decay
  study's own `SIGNIFICANT_T = 1.65` (MANTENER is now reachable by more strategies: on
  `Test_Calib_USDJPY_H1` 565 clear 1.65 where 232 did), its «t máximo», and any `criteria.yaml`
  rule on `gate.scorecard.degradacion_t` (none today).
- **Owner's call:** which t step 8 judges on. The red team recommends `drift_excess_t` (limbo ≥ 1.65,
  pass ≥ 2.33), one line for every asset and side; the calibration proposal's R8 lines were written
  on the old scale and its side table becomes unnecessary.
- **Still open — the null is not on the same statistic.** `AlgoData/scratch/null-fpr-2026-10-01`
  books closed trades and used the bugged formula; SQX's curve is the daily low with the floating
  in (#88). Until the null is recomputed on `trade_t` / `drift_excess_t` (and re-costed to match a
  random-generation population), its FPRs are upper bounds by 2–4× and real/null ratios ~3× low.
- **Still open — `worst_day_r` is low to low** (#88), not start-of-day to intraday low; an exact
  daily-loss figure needs trades + M1 (`portfolio/common/construct/equity/`).
- Reports written before 2026-10-02 (`gate/scorecard.parquet`, `decay/`) keep the old t; the 23
  `Test_Calib_*` gates were re-run on 2026-10-02, nothing else was.

**2026-10-04.** 2026-10-04 point 1.5 measured: old 1.65 = 1.92 on the corrected scale (oos1 of 5.16 years); no live rule reads that t (min_t = 0.0); the live rule is R3 drift_excess_t ≥ 2.33, FPR under the null 0.00 % [0.23] with costs and 0.58 % [1.08] without; at 1.65 0.07 % [1.8] / 3.6 % [5.8]. The null of 2026-10-01 no longer exists; scratch/null2 replaced it with costs identical to today's asset cards (cost drag 0.84-1.04× six real populations, re-costing moves FPR ≤ 1.3×). Session recommendation: it barely matters, judge on drift_excess_t as R3 does, re-run nothing except XAUUSD/OOS if still used. Owner questions: still using XAUUSD/OOS? which null defines edge, with or without costs? is the XAGUSD card final (not on #76's list)? Card: knowhow/research/gate-t-scales.md; tables AlgoData/scratch/null-fpr-2026-10-04/.

## Constraints discovered while investigating

- **SQX rewrites every `project.cfx` on save/exit.** All 14 project files were restamped within the
  same second (`14:33:43`, 2026-09-02). Editing a `project.cfx` on disk while the GUI holds that
  project **will be silently overwritten**. Config edits must be made in the GUI, or on disk only
  while SQX is not running.
- `project.cfx` is a plain ZIP: `config.xml` + one `<Type>-Task<N>.xml` per task. Safe to *read*
  at any time.

## 89. 🟡 What the 2026-09-30 H1 workflow run (steps 5-26) left open
📓 2026-09-30, `Test_USDJPY_donchianUpperCrossUp_H1` run end to end through the window's launchers
(report: `scratch/informe-2026-09-30.md`). Fixed in that task and not listed here. Still open:
- **`tests/test_ui_strategy.py` fails**: it expects `meta["backtest"]` (the per-task costs the
  ficha's metadata warns about, `ui/desktop/workspace/fichameta.py`), which
  `sqx.inspect.strategymeta` never returns. Another session's unfinished work; not touched.
- **Costs changed mid-run**: the WFC legs were configured with USDJPY's old single spread (0.65);
  the asset now carries 0.49 / 0.59 / 1.16 per segment. Steps 16.5-24 ran on the old legs, kept
  for consistency within the run.
- **MC Retest ingest**: two level tables unusable, «run cut short» — `bar/4.3.53`, `ohlc/8.13.72`
  (after the fastutil NPE relaunch, `knowhow/sqx-drive/mcr-nullpointer-fastutil-transient.md`).
- **Step 23 control «madre reconstruida»** printed an empty table: the mothers came from
  `CrossTF_Mothers`, whose files keep no build/oos1 result to compare against.
- **Step 25 reads the mother without its stop**: step 24 recommends X but nothing harvests the
  stopped version in the shape `edgeCost` reads; the run read the `Results` harvest.
- **Replicación never runs in a workflow project**: it compares one build's conclusions against
  other builds, and a workflow project has one. The page now says so instead of «no ha corrido».
- **Filtros candidatos asks for ≥200 strategies**; after the step-8 cut the population is 60.
- **A study whose result lives in another databank reads «Sin resultado todavía»** on every
  other databank's strategy page: Lectura conjunta (step 20, filed under `WFM`), Exposición
  (`CrossTF_Mothers`), Stop loss ATR and the optimisation studies (their work folders), opened
  from Cross Market or Cross TF. Results pair by identity, and a name pairing is only ever
  offered as a jump (`ui/daemon/runner/offer.py`) — today only for a study the runner refuses.
  Proposal for the owner: offer the same jump when the study is not refused but its result is
  elsewhere. Seen in the 2026-09-30 walk (`scratch/run0930/shots/w4`).
- **Hantec after the clock fix still fails rows 1/3a/5** on the three USDJPY mothers (drawdown
  0.292 % SQX vs 0.228 % MT5 on 10.9.72): not the clock any more (`clock_h` 0 on all six) —
  costs or Hantec's history, to diagnose.

## 86. 🟡 Audit 2026-09-30: exports without manifest, a `migrate` code_version, two files over 250 lines
Opened by the unattended docs pass from `audit/2026-09-30.md`. None is a documentation error; all wait for a decision or for in-flight work.
- 📓 **Exports without a root manifest** under `AlgoData/raw/`: `Test_USDJPY_donchianUpperCrossUp_M30/SPP_IS/2026-09-27`, `.../SPP_OOS/2026-09-27`,
  `XAUUSD/SPP_IS/2026-09-19`, `XAUUSD/SPP_OOS/2026-09-19`, `XAUUSD/WFM/2026-09-10` (audit list cut at 5). Reproduce: `python3 tools/daily_audit.py`.
  Fix: a root manifest written by that exporter, or declare the gap accepted. Not resolved — the exporter is code.
- 📓 **One manifest has `code_version` = `migrate`** (not a commit; `git cat-file` fails). Not located. Find: `grep -rl '"migrate"' ~/Desktop/AlgoData/raw --include=manifest.json`. Declare or rewrite.
  Located 2026-10-01: `raw/XAUUSD/Results/2026-09-03/manifest.json` holds the single string `migrated from AlgoProject_Old, pre-git` — the audit's `migrated`/`pre-git`/`AlgoProject_Old`/`from` are that one value split by its grep (🔬 grep). The 21 `<hash>-dirty` ones resolve after stripping the suffix.
- 📓 **`tools/checks.py` file-length** — resolved: audit 2026-10-01 reports 982 files, 0 problems.
- 📓 **Custodian log 704 MB**: `log_2026_09_29.log` 526 MB, ~220k × `TradingException: Setting 'TradingSetup.StrategyClass' is not set` in `WFSimulationJob`.
  Same storm as `knowhow/eng/log-retention.md`; the archiver + prune handle it (SQX config is the owner's). Repeated 2026-09-30: `log_2026_09_30.log` 167 MB, 70,212 `StrategyClass` lines; custodian folder 861 MB (audit 2026-10-01). Archiver + prune handle it; cause stays with the owner.

**2026-10-06.** Manifests: four of the five nightly findings were false positives (the manifest sits beside the data in `spp/`, `wfm/`, `wfc_pairs/`, `strategies/`; the auditor's instruction demanded it at the root and is rewritten); the fifth, a torn trades export of the retired `Test_USDJPY_donchianUpperCrossUp_M30/SPP_IS/2026-09-27`, is deleted, and `daily_audit.exports_without_manifest()` returns []. The `export_trades` wipe of the SPP folder was already fixed in `89e3a7c`; `tests/test_export_manifests.py` now proves it. The pre-git `code_version` is a named exception (`core.manifest.PRE_GIT`). Worker logs: the prune deleted by age only, so archived storm logs stayed (2.6 GB); it now drops an archived past-day log above 20 MB at any age (SQX_w1 893 MB → 38 MB, SQX_w2 1.8 GB → 5.7 MB).

**2026-10-06.** The cause of the log storm is being removed on the owner's order: the custom columns `ParameterCount` and `DoFRatio` (they raised on every WF step). Done on the conductor and verified on two starts (`knowhow/columns/param-count.md`); Python computes both (`core.sqxview.frame`). PENDING on the custodian — it was running another session's job: with it stopped, `python3 ~/Desktop/AlgoData/snapshots/sqx-columns-2026-10-06/drop_columns.py ~/Desktop/SQX_w2 ~/Desktop/AlgoData/snapshots/sqx-columns-2026-10-06`. PENDING on the master, the owner's call: `Build-Task3.xml` of his projects AUDJPY, EURUSD and USDJPY carries a `ParameterCount` column value, which removing the class may break. Four archived storm logs over 10 MB deleted from `AlgoData/logs` (131 → 53 MB).

## 87. 🟠 Portfolio construction engine — M0-M2, F1 and the F2 engine built 2026-09-30; the owner's calls gate each milestone

The plan is `portfolio/PLAN.md`; the order is in `portfolio/CLAUDE.md` (M0-M2 → F1-F5 funded → M3-M8
real → M9 paper OOS). Built so far: M0 code, M1, M2, F1 and the F2 engine (bullets below); F3 onwards
and M3-M9 are not. What each milestone waits on:

- **M0 (the development pool):** the owner's go-ahead to archive survivors (the archive reads SQX
  install files and the daemon); PLAN §12 Q2 (where `oos2` comes from — the archive holds only IS and
  `oos1`), Q13, Q14; `DECISIONS.md` #10. Development assets: USDJPY and XAUUSD (owner, 2026-09-30).
- **M1-M2:** Q1, Q6-Q9, Q15 (Q3-Q5 are settled for the funded path by the firms' rules, §14.4).
- **F1:** encargo 33 §6 questions 1-3.
- **F4 / M5:** Q11. **M3:** `DECISIONS.md` #2 (real side), Q10, Q12, Q16. **M8:** `DECISIONS.md` #5.
- **Settled 2026-09-30:** floating from M1 **wicks**, longs and shorts alike (SQX's MAE reproduced on
  2,094/2,094 trades, `knowhow/export/mae-mfe-from-m1.md`); search at M5, finalists and verdict at M1
  (`knowhow/perf/intraday-floating-resolution.md`); Monte Carlo T1 + T2 + D, the most pessimistic
  decides, block length measured; the funded portfolio chosen by P(pass) inside the engine
  (`DECISIONS.md` #13, delegated to the session); OOS correlation is a verdict check, never a selector.
- Index CFD M1 bars are not in `AlgoData/bars/`; the owner imports them when needed.
- **Answered 2026-09-30 (second session):** Q1, Q2, Q4, Q6-Q9, Q12-Q15, Q17, `DECISIONS.md` #10,
  encargo 33 §6.1-§6.3 — `portfolio/PLAN.md` §12 «Answered». Still open: Q10, Q11, Q16,
  `DECISIONS.md` #2 (real side), #5, #12, encargo 33 §6.4 and §6.7. Hantec's server clock taken as
  New York + 7 h, **unconfirmed** — read it from Hantec's MT5 terminal when the bridge is up.
- **Built 2026-09-30: M0 code, M1, M2, F1** (`portfolio/PLAN.md` §9 status, chapters 77-78 in
  `11-cartera.pdf`). Found on the way: SQX's daily curve is the day's LOW (#88); the tail filter is
  biased −0.46 between independents and runs one-sided; only 75 % of independent pairs pass every
  filter on a 10-year build (`knowhow/research/pair-filters-false-rejection.md`).
- **F2 engine built** (chapter 79): stage A on 48 cores. Its first real run needs pool members that
  carry the step-24 stop (SL = X·ATR(20), X = p90), archived as their own identity — none yet.
- **Next: F3** (stage B: exact M1 joint intraday, T1/T2/D Monte Carlo, risk per phase) after a real F2 run.
- **Development pool waits** for `Test_USDJPY_donchianUpperCrossUp_H1` (custodian, at 16.5 on
  2026-09-30 11:20) to finish: no mother has oos2 trades yet. Then `candidates.py` lists the
  archive commands and the owner archives.

**2026-10-04.** The Council decided the pending calls on the owner's delegation (`portfolio/PLAN.md` §12, `portfolio/DECISIONS.md`): Q10 (a) signed ranks of RAR %, R-cubed, gain-to-pain, P(losing year); Q11 (d) oos1 against the 95th percentile of 10,000 random admissible portfolios, then deflated Sharpe > 0 on oos2 read once; Q16 (c) provisional; #2 size from the 10k account at minimum lot; #5 never rebalance; #12 no probation label; after oos2, live incubation. **M0 pool:** the 30 mothers of `Test_USDJPY_donchianUpperCrossUp_H1` carried to 16.5 are archived (from files with `--sqx`, the project is on no install; none carries the step-24 stop; no pool declared). `candidates.py` now lists 182,464 commands, 182,220 of them `Test_Calib_*` step-8 survivors — not archived, the pool's extent is the owner's. **M3 built** (`real.py`, `search/objective.py`, `exhaustive.py`, `choose.py`, `admission.py`, `trials_real.py`, `verdict/metrics.py`; `tests/test_portfolio_ranks.py`, chapter 96): its first real run needs a declared pool whose members carry the step-24 stop and the owner's `real.losing_year`. **M5 specified, not built; nothing read oos2.** Eight readings left open are listed in PLAN §12 «Readings the Council's answers leave open».

**2026-10-05.** 2026-10-05: the whole `portfolio/` module is built and tested on the relaxed `Test_nikkei_ref` pool under a quarantined TEST root (`portfolio.testroot.build`, env `ALGO_DATA_ROOT`) — M0-M9 and F1-F5 per `portfolio/PLAN.md` §9, with the UI zone (`ui/daemon/portfolios/`, `ui/desktop/portfolios/`). The owner answered R1-R8, Q16 (candidates enter in sequence), F3 `shared_of`, F4 `pass_measure`, rebuy, haircuts and `shift_minimum: metric`; so the line above listing Q10, Q11, Q16 and encargo 33 §6.4/§6.7 as open is superseded (Q10/Q11/Q16 answered; Q11 readings and the unseen data of §6.7 stay open, see PLAN §12 «Readings the Council's answers leave open»). NO real result exists: no real pool run, no portfolio run or ledger row in the real root, incubation (M9) not running, no real oos2 read. Still null: `funded.open_risk_cap`, `stageb.t1_gap`, `verdict.pass_percentile`, `wf.confidence`, `incubation.figure/history/band`, the nine funded-sim inputs (#85). Unfixed findings: #104.

## 90. 🟡 The autopilot (`pipeline/autopilot/`) — phase 1 ran end to end 2026-10-01 (6 → 16), its holes fixed

Owner, 2026-10-01: a fully automatic, fast workflow; binary criteria with three outcomes (pass /
limbo / fail), a limbo goes on marked, a step without criteria lets everyone through; meanwhile a
random draw of 5 at step 8 only; not `ALGO_AUTONOMOUS`. Phase 1 = steps 7 → 16; tested offline
(facts, criteria, plan) on `Test_USDJPY_donchianUpperCrossUp_H1`, never a real run.

- **First real run done 2026-10-01** (`Test_XAUUSD_timeRangeBreakout2_M30`, crossmarket on XAGUSD
  only — UKOIL was mid-conversion): 6 → 16 in ~51 min after a build stopped by hand at 571
  strategies. Costs in `knowhow/perf/autopilot-dead-time.md`. Fixed the same day: consecutive SQX
  steps share one start (`run.merged`, 6+7), `--own-log`, the YAML `on:` key in `judge.settings`.
- **Fixed 2026-10-01 — a refused study counted as done:** the autopilot runs
  `chain.python_step(strict=True)`, a refusal is a failure.
- **Fixed 2026-10-01 — the MC Retest ingest refusal:** SQX stores each trade in whole cents and
  counts losses on the full figure; with the %-annual swap a 0-cent trade is often a fraction of a
  cent lost. `integrity.zero_readings` reconciles a stored zero as any of zero / loss / win.
- **Fixed 2026-10-01 — re-exports at every stop:** the fingerprint read only settings.xml
  order-free; `MonteCarloManipulation_Results.xml` moved all 571 on a bare start+stop
  (`state._entries` now reads every XML entry). The MCR databanks' trades are no longer exported
  (no study reads them).
- **Decided 2026-10-01 (owner) — build cap, whichever first:** `Trade_` 10,000 strategies or 180
  min, `Test_` 300 or 10 min (`databank.caps`, `builder` defaults). SQX stops on the count; the
  minutes are enforced by `ui/daemon/advance/buildcap.py`, and the autopilot then runs the OOS
  the stopped project skipped.
- **Decided 2026-10-01 (owner) — `profitShape` and `entryQuality` run after step 8's cut**, on its
  survivors only (`pipeline/autopilot/run.py` `AFTER_CUT`); they were 200 of step 8's 297 s on all
  571. The window's «Correr workflow» still runs them before its stop at 8.
- **Decided 2026-10-01:** step 12 judges each mother by her siblings and cuts `CrossTF` (losers
  and every scaled sibling), so step 13's refill of `CrossTF_Mothers` holds only the passing
  mothers, unscaled. A fact missing for a strategy → limbo (owner: odd, but limbo).
- **Decided 2026-10-01:** step 14 cuts `MCR 8 Stress` (what SPP IS reads), step 16 cuts `SPP OOS`
  (what the WFM reads; 16.5 takes the survivors from it and their SPP IS counterparts).
- **Blocks the «compared with the original» facts of step 12:** the baseline cell had 0 trades on
  all 30 mothers of the 2026-09-30 run (§89, the empty «madre reconstruida» control).
- **Phase 2** (16.5 → 20, mother by mother): the mothers are those left in `SPP OOS` after the
  step-16 cut, each matched to her counterpart in `SPP IS`; the variants are designed from the
  metrics of the combined backtest (owner, 2026-10-01: «no es necesario coger solo SPP OOS»).
  Today `pipeline.run.mothers` takes every mother of the SPP export and the brief reads only IS.
  `pipeline/recipe.yaml` also fails as written —
  `ran` lacks `--project`, `wfc`/`cscv` lack `--family` (§50), `--chart` hard-codes XAUUSD.
- **Phase 3** (21 → 26): the stopped version is not harvested for step 25, no pool for 26 (§89, §85).
- **Overlapping two populations** (one in SQX, one in Python) only if the measurement shows the
  dead time is large.


## 93. 🔴 Criteria of steps 6 and 8 proposed 2026-10-02 — four owner decisions, 15 assets unmeasured

`assets/_study.yaml` (step 6) and step 8 of `pipeline/autopilot/criteria.yaml` carry an agent's
proposal, calibrated in `docs/AgentPDFs/criterios-pasos-6-y-8-2026-10-02.md`. Open:

- **Owner's decisions** (dossier §1): the trades-per-year floor (written as fail < 20, limbo 20-40,
  pass >= 40 on `is_trades_per_year`; he prefers 40-50 as a floor); `dev.on` still true, so the
  rules apply and 5 survivors are then drawn at random; the risk per trade on funded accounts.
- **Sessions: done 2026-10-02 for 15 of the 16 cards that name one.** `doctrine.borrow_session` now falls
  back to a copy of the master's `user/data/data.db` (`sqx/projects/sessiondb.py`,
  `knowhow/costs/sessions-live-in-data-db.md`); a real EURUSD H1 project carried `EURUSD_ftmo` from it.
  The three `session: null` cards got theirs the same day (owner: FTMO's for every asset) —
  `XAGUSD_ftmo`, `UKOIL.cash_ftmo`, `USOIL.cash_ftmo`; XAGUSD and UKOIL build.
  **The feed has the same fallback since 2026-10-02**: no project carries `DAX40_M1` or
  `USOIL.cash_M1`, so `resources.definitions` writes their `<Symbol>`, `<InstrumentInfo>` and
  `<Broker>` from the registry (`registryxml.definitions`). All 19 assets now build; DAX40 and USOIL
  were built H1 into a temp install, none of the 17 new ones has been RUN in SQX yet.
- **Untested**: a `Trade_` build fills the databank in minutes and then replaces by IS Ret/DD for
  the rest of its 180 minutes — a selection nobody measured (test: 180-min full build against a
  6-min one). The A/B of floors inside the build is one build per arm.
- **Not a fact yet**: the IS profit factor (a `PF >= 1.10` rule at step 8 needs it).
- **Spent**: `oos1` of USDJPY and XAUUSD was read to choose these thresholds; freeze them before
  the next build. `oos2` untouched.
- **Data**: the calibration left ~28 `Test_Calib_*` trees under `AlgoData/{harvest,reports,raw,metrics}`
  and `AlgoData/scratch/{calib_*,null2,null-fpr-2026-10-01}` — #92's budget. Delete once the
  owner has decided.

- **Condition count (rule 14) and palette (rule 15): in the builder since 2026-10-02.**
  `buildrules.what_to_build` writes entry 1..2 / exit 1..2 for a Simple Strategy (`builder --simple
  long|short`, `--random` for the twin) and `0..(2 − fixed)` per side for a template; the builder
  refuses two free holes on a side (`freeShellLong`/`freeShellShort` are now refused: use
  `--simple`); `buildingblocks.rewrite` never switches on a stop/limit level or a clock block, and
  `buildingblocks --count` prints what a Build carries (`tests/test_condition_count.py`,
  `tests/test_builder_simple.py`). Still open:
  - **No Simple Strategy project has been started in SQX yet** — files only. The first population
    confirms SQX takes it (`knowhow/authoring/simple-strategy-build-xml.md`).
  - **A template's fixed idea is a hole bound to a one-item group**, and SQX has one condition range
    for every hole of a side: such a side is written 1..1 (idea + exactly one random), not the
    owner's 0..1. Whether a bound hole at min 0 keeps its block needs one short build; until then
    "the idea alone" is never built from a template.
  - Owner: in a Simple Strategy the exit rule is drawn in ~50 % of strategies (`_ExitRule_`
    probability 50, as in his own project) and then holds 1..2 conditions — or must every strategy
    carry one (`exits.condition_required`)? And: are `SessionHigh/Low/Open/Close`,
    `HighestInRange`, `CBlock_TimeBreakout*` clock blocks for rule 15? Today only SQX's
    «Bar And Time» natives are refused.
  - The 28 calibration populations exceed the cap and used the broad palette (842 blocks) — they
    must be rebuilt per family before the criteria are taken as final.

**2026-10-03.** 2026-10-03/04: steps 6 and 8 recalibrated (116 base cells, 201 populations, red-teamed) — dossier `docs/AgentPDFs/criterios-pasos-6-a-12-2026-10-04.md`, PROVISIONAL, owner's approval pending; proposals written in `assets/_study.yaml` (ceiling 75/yr, no floor beyond 10/yr, no PF/RetDD) and `pipeline/autopilot/criteria.yaml` (step 8; steps 10 and 12 still `rules: []`). Cards: `knowhow/research/{step6-floor-vs-step8-yield,is-filters-inside-the-build,oos1-oos2-persistence,drift-term-biased-by-side,crosstf-mother-sibling-dependence,crossmarket-effective-markets}.md`. Still open: (1) long builds (180 min, cap 10,000) with a full databank — no IS filter was tested there; (2) the gate's drift-term correction is proposed, NOT applied (`drift_excess_t`, and `crossmarket/simulate/excess.py` with it); (3) `wfc.py` gives extra markets the main's dates; (4) 7-11 % of strategies change identity between the build and the OOS databank (name join; fingerprint agrees 99.7-100 % on 3 populations); (5) the crossmarket and crossTF studies hard-code their window, so oos2 is read from raw exports; (6) `assets/_policy.yaml` oos2 end 2026-09-30 is past the last bar of XAUUSD, XAGUSD and HK50 — an OOS2 task cannot start (`knowhow/sqx-drive/cannot-start-unresolved-past-data.md`); (7) 31 H1 base cells have no oos2 (`oos2_job.sh` not run).

**2026-10-04.** Owner, 2026-10-04: the calibration study these criteria were derived from was run at a wrong spread («un fiasco») and its data, registry rows and ledger rows were deleted on his order. The step 6 and 8 figures in assets/_study.yaml therefore rest on nothing that exists any more: do not sign them and do not build on them; they need a new calibration at the recalibrated spreads (commit 3b71384), or the owner's own numbers. The oos2 look of that study happened regardless of the deletion.

**2026-10-06.** Cleanup by the owner's order: nothing named `Test_Calib_*` is left under `harvest`, `reports`, `raw` or `metrics`, and `AlgoData/scratch/{null2,null-fpr-2026-10-04,close-curve-2026-10-04}` are deleted, as is the card `research/step6-floor-vs-step8-yield` (its numbers came from the invalid calibration). The sentence above about ~28 remaining trees no longer holds.

## 95. 🟡 Twelve tests set aside in `tools/audit_tests.py` — each with its reason, so the skip list has an owner
📓 2026-10-02. The mechanical audit runs every `tests/test_*.py` (105 on the day) and lists in `ASIDE`
the ones it does not count as failures: 92 passed, 13 set aside. The thirteenth, `test_thresholds`,
is #94. The twelve below are not bugs of the audit; each is either another session's work in
motion or a drift that needs a decision. The audit prints them as «apartadas» and says «PASSES:
remove it from ASIDE» when one recovers, so the list cannot rot silently. Reasons as written in
`tools/audit_tests.py`, all dated 2026-10-02:

| test | why it fails | whose / what clears it |
|---|---|---|
| `test_commission_segments` | Darwinex's commission is PercentageBased 0.005 in the asset cards; the donor's Build and Retest Setup still say SizeBased 5.0 | cost cards in motion (`assets/_build.yaml`): align the donor or the test |
| `test_feedquality` | `calibration.json` is keyed by the old feed names (`XAUUSD_DukasM1_Infinox…`); the feeds became `XAUUSD_M1` on 2026-10-01 | recalibrate or rekey the file |
| `test_mt5verify` | 5 assertions fail while `mt5/verify` (`firms.py`, `judge.py`, `run.py`) is being rewritten | the session rewriting it |
| `test_portfolio_build` | `AttributeError: RangeIndex.to_period` in `portfolio/common/construct/equity/matrix.py` with the test's fixture | a code or fixture bug, not a one-line fix |
| ~~`test_portfolio_mtm`~~ | **passes since 2026-10-04**: the drift was the feed's clock alone (Asia/Jerusalem → EETUS); the golden is pinned on its own clock, bar still 0.99 (MAE 1.000) | out of ASIDE; open decision: production still reads clock and commission live for archived strategies (`knowhow/export/archived-trades-vs-reclocked-bars.md`) |
| ~~`test_portfolio_universe`~~ | **passes since 2026-10-04**: 3,983 of 3,983 days within 1 $ (max 0.16 $) on the archive's clock; the current feed has its own golden, `test_portfolio_golden_current` | out of ASIDE |
| `test_strategymeta` | the golden's `asset_card_sha256` is not the sha of `assets/symbols/XAUUSD.yaml` after the cost-card edits, and `strategymeta` reads the golden strategies differently | re-freeze the golden after the cost cards settle |
| `test_ui_columns` | the databank column chooser's default order changed while `ui/daemon/databank/` is modified | the session working on it |
| `test_ui_research` | the research board's passing cells differ | `studies/research/board`, another session's work in progress |
| `test_ui_results` | the results catalogue does not match `studies/` (board, marketProfile, memory, monteCarlo) | `ui/daemon/results/` and `studies/research` in motion |
| `test_ui_sqxconfig_studies` | the ledger changed more than its three lines (sealed 2026-10-02); the test's expectation of `ledger/thresholds.yaml` is out of date | update the expectation |
| `test_ui_strategy` | strategy meta has no `backtest` key — the same failure as in #89 | `ui/daemon/` modified by another session |

Decision for the owner: none yet. Each row closes when its test passes again and is removed from
`ASIDE`; close this issue when `ASIDE` is empty or holds only entries with an open OPEN number.
Reproduce: `python3 tools/audit_tests.py` or the single file (`python3 tests/test_<name>.py`, or
`python3 -m pytest -q tests/test_<name>.py` when it has no `__main__`).

**2026-10-06.** `test_feedquality` and `test_ui_columns` pass and left `ASIDE` (8 remain). The runner now sends a file to pytest only if it has no `__main__` and defines `def test_`: eight nightly false failures gone. Fixed today: `test_builder_feedswap` (no live install read), `test_ui_shell` (a shared ruamel `YAML()` was loaded from several threads — lock in `core/assetyaml.py`), `test_ui_blocks` (three population reports per study, 103 s), `test_ui_cmdpalette` (a real window bug in `studypage/picker.py`), `test_ui_screen`, `test_ui_tearsheet`, `test_ui_campaign`, `test_ui_studypage` (its batch fixture now a kept `Trade_` project).

**2026-10-06.** `test_ui_blocks` draws every population report again (307 results, 196 s on a loaded machine) plus three strategy reports per study, long tables cut to 200 rows. What made it slow was the window, not the test: `bars._geometry` measured 1,000 labels on every paint and mouse move, fixed (`knowhow/ui/qt-painting-traps.md`).

## 96. 🟡 `core.surface.trials.independent` over-counts when one family holds more than half (rule kept, owner 2026-10-02); the raw crash is now a clear error

Found 2026-10-02 contrasting with tschm/jsharpe (encargo 42, C1). On balanced blocks it is exact
(2, 4, 8 of 40 variants). With 30+5+5 the «no cluster above half» rule refuses the true split
(k=3, silhouette 0.531) and returns 14 (silhouette 0.147); one blob of 40 returns 16 (silhouette
0.014). The deflated Sharpe's bar goes from 0.85σ to 1.74σ: harsh side, but an artefact. With no
admissible split up to `k_max` it raises `ValueError: max() arg is an empty sequence` (one blob,
`k_max=10`; cscv's 40 hides it). Owner's call: keep the rule and report the silhouette as the
tell (< ~0.2 = no structure), or let a dominant cluster stand. Same contrast: our
PSR/MinTRL/DSR follow the 2012/14 convention, jsharpe the 2025 one; arithmetic agrees.

**Owner's decision, 2026-10-02:** KEEP the half rule (count unchanged in every case); the silhouette is
the tell, below ~0.2 the count has no structure (a reading aid in docs, no threshold in code); keep
the 2012/14 PSR/DSR convention. **Done:** with no admissible split up to `k_max`, `independent` raises a
clear `ValueError` (k_max, «every split leaves a cluster above half») instead of `max() arg is an empty
sequence`; `tests/test_inference_vs_jsharpe.py` pins the new text. The silhouette already travels in
the dict `independent` returns (`cscv.json` › `trials`, `ledger.trials.population_n_eff`); no signature
changed. **Open:** nothing prints the silhouette next to the count in a window or a report line.
→ `knowhow/research/trial-count-half-rule.md`, `knowhow/research/psr-dsr-two-conventions-jsharpe.md`

## 100. 🟠 Literature scout built 2026-10-02 — owner decisions pending, 8 questions and 8 entries without a condition

`studies/research/literature/`, `/literature-scout`, `bin/daily-literature-scout.sh`; day one in
`knowhow/market-profile/literature-scout-yield.md` (67 papers read, 9 useful, 17 entries, 1 measured: no cell passes).

- **Cron installed 2026-10-02**: `0 7 * * *` (backup `AlgoData/logs/crontab-backup-2026-10-02c.txt`). Owner:
  spend what reading needs — opus reads, sonnet triages, `run.budget_tokens` 3M is only a runaway guard.
  The first unattended run (2026-10-03) is the first with the paged search: check its log.
- **Sources** (owner, 2026-10-02): repositories on with the grade `code repository`; Oxfordstrat, Quantpedia
  and AQR on. traders.com, SSRN, Alpha Architect and Semantic Scholar refuse a script; OpenAlex has a free
  daily budget per IP (a free API key would lift it — the owner's to get).
- **20 entries wait on his answer** (`python3 -m studies.research.literature.report`, the `PREGUNTA` blocks;
  `--answer ID N`), then a session writes their measures (`scout measure`). At this rate the questions
  outgrow what he can answer: whether the reader should ask less is open.
- **10 entries have no measure**: most state no parameters in the text read (five point to Sullivan et al.
  1999), one tests a 354-pair grid, the newest need conditions `rules.py` lacks (Keltner, Hull, MACD, ADX).
- **The profile's top-up was stopped half-way on 2026-10-02** (RAM conflict with the calibration queue):
  only DAX40 and DJ30 carry TR-65's six measures and the three corrected ones (`slow_d50_200_run`,
  `fast_d5_20_run`, `fast_d5_20_quiet_run`, inverted until that day; old rows dropped, backup
  `profiles/cells-backup-2026-10-02-meanorder`). `measures.csv` and `assets/FAMILIAS.md` still show the old
  rows. The daily run completes it with 4 workers when 25 GB are available; else run
  `nice -n 19 python3 -m studies.research.marketProfile.report --top-up` and `--familias` after the
  calibration ends (~05:40 UTC 4 Oct).
- `tools/manual.py` refuses to build while chapters 85, 87, 88 and 89 (other sessions') have no family:
  the PDF of family 04 was built alone for chapter 90.

## 102. 🟠 Knowhow cards filed in the wrong domain — found by the weekly quality pass, 2026-10-04

The pass does not move cards (it would change `see:` slugs and the per-domain indexes). Candidates, judged from
their `q:` and header only (🤔: confirm by reading each card's callers):
- `knowhow/market-profile/` holds six cards that are not about the market profile: `literature-same-paper-short-title`,
  `literature-scout-yield`, `paper-search-sources`, `verbatim-quote-matching` (→ `research/`, literature scout);
  `typed-failure-causes`, `hypothesis-sheet-vs-build`, `ideas-are-ledger-trials`, `reviewer-adds-no-trials`
  (→ `research/` or `pipeline/`, the idea/autopilot memory).
- `perf/window-waits-off-gui-thread` is a Qt/window fact (→ `ui/`).
- `eng/` holds study facts: `monkeyexcess-needs-oos-partner`, `population-signs-a-different-config-than-strategy`,
  `stale-signs-with-the-runners-overrides`, `decay-needs-build-and-retest`, `isoos-filters-read-the-harvest`,
  `step25-reads-a-harvest-of-the-traded-version`, `studies-reread-build-yaml` (→ `pipeline/` or `research/`).
Decision needed: move them (then rerun `python3 tools/knowhowmap.py` and fix every `see:`), or declare the domains broader.
Also left: `locations/xauusd-corpus` (🤔, 231 strategies, old export) and `export/exits-and-m1-library` (🔬, 757 strategies)
describe two XAUUSD corpora; neither can be recomputed for the first (OPEN §12) — the owner may retire the older card.

## 104. 🟡 Portfolio build 2026-10-05: six findings left unfixed — found while running the module on the Nikkei test pool

📓 2026-10-05, the build of `portfolio/` (impl log phases 0-6). Each is found, not fixed; the first four are the code's, the fifth is pyarrow's, the sixth predates the build.

1. **The universe cache ignores code changes.** The folder `<root>/portfolio/universe/<pool hash>-<config fingerprint>` is keyed by the pool and the whole config, never by the code: after an engine change a stale folder gave P 0.340 against 0.338 (`portfolio/common/construct/equity/README.md`). Every distinct `--set` (even `real.*`) also builds a new 4.6 MB folder. Fix: key on a code version, or say so on reuse.
2. **Sizing takes the latest archived version, not the pool's frozen one.** `size_members`, `funded._member_meta` and `funded_b.load` call `archive_read.versions(identity)[-1]`; a pool is frozen by `identity@version`, so a re-archived member would size with another file than the one the pool declared.
3. **The GA's rank score saturates on pools above `real.exhaustive_max` (100,000 combinations).** `real.rank_reference: seeds` ranks against greedy maximal cliques; anything better than all of them scores 1.0, and the GA stops on stagnation without trying the small K (planted pool: returned {A, B, N0, N1, N3} where the exhaustive search gives {A, B}). The Nikkei pool is exhaustive (103) and unaffected. The owner's: raise the limit (1,000,000 ≈ 11 min on one core) or rank against random cliques of every size (`portfolio/PLAN.md` §12 reading 9). The funded GA also re-evaluates duplicates (4,500 evaluations = 58 distinct of 103) and counts them in the ledger's `n_scored`.
4. **`funded_b` reruns give different winners and overwrite their folder.** Three runs on the same stage-A run gave three winners (finalists within 0.003), each writing the same `runs/<stamp>_<pool>_<plan>` folder (the stamp is to the minute, `exist_ok`), so the verdict's chosen portfolio is lost on a rerun and the F4 oos2 read can be refused for «other members». Fix: a seed recorded in the manifest and a folder per run (or refuse an existing one). Which near-tied finalist is «the» portfolio is the owner's.
5. **pyarrow 25.0.1 `pd.read_parquet` aborts at interpreter exit under load** (exit 134 after the program's own «TODO OK»; 8/80 runs with 40-60 copies at once, 0/10 quiet). `pa.set_cpu_count(1)` or `pq.ParquetFile(p).read()` gives 0/288; 178 `read_parquet(` call sites and no shared reader, so the choice is project-wide. Card `knowhow/eng/pyarrow-read-parquet-aborts-at-exit-under-load.md`.
6. **`tests/test_portfolio_build.py` fails with «Ningún miembro del pool concilia con SQX»** — before this build too (the archived USDJPY `4d679e0c…` on the old feed no longer reconciles); it is set aside in `tools/audit_tests.py`. Not caused by the build.

**2026-10-05.** 2026-10-05, the walk of the PORTFOLIOS zone (`tools/uiinventory.py`). **Fixed, each with its test:** (1) the universe folder is now keyed `<pool hash>-<config fingerprint>-<code hash>` (`construct/equity/store.py`, `tests/test_portfolio_universe.py`) — a `--set` still makes its own folder; (4, the overwrite half) every run folder is made exclusively (`core.manifest.fresh_dir`: `_2`, `_3`… within one minute) and a second stage B on a run that holds one goes to a run aside with `stage_a_run` in its manifest, the first left byte for byte (`funded_b.target`, `tests/test_portfolio_verdict_funded.py`; seen through the window on a disposable root); (5) the planted-pool tests take `pa.set_cpu_count(1)` from `tests/portfolio_planted.py`: 9 of 60 aborts before, 0 of 180 after — nothing project-wide changed. **Investigated, not fixed:** (6) is a stale fixture, not portfolio code — `USDJPY_DukasM1_the5ers` now maps to `USDJPY_M1` on the EETUS clock (commit 1f22b6f) while the archived trades are stamped Asia/Jerusalem, and the card charges 5 $/lot since d8e1ffe where the strategy was built at 0: re-stamped and at commission 0 it reconciles 1.0000/1.0000, max gap 0.2 $ (as archived 0.44/0.39). Pinning the fixture to its archive-time conditions or moving it to a strategy archived on `USDJPY_M1` is the owner's. **Still open, the owner's:** (2) which archived version sizes a member, (3) the rank reference above `real.exhaustive_max`, (4) which near-tied finalist is «the» portfolio (no seed recorded yet).

**2026-10-05.** Item 3 decided (owner, 2026-10-05, «sube»): `real.exhaustive_max` is now 1,000,000 combinations (~11 min on one core at the limit); `portfolio/common/construct/search/README.md` and `portfolio/PLAN.md` say so; above the limit the GA still runs and its rank score still saturates — still open. Item 6 (owner, 2026-10-05: «Usa las condiciones más actualizadas que tenemos»): the test must run on today's conditions, no re-stamping shim, no skip. Found: nothing in the archive reconciles under today's conditions. The only archives after 2026-10-01 are the 30 mothers of `Test_USDJPY_donchianUpperCrossUp_H1` (2026-10-04, step 16.5), all on feed `USDJPY_DukasM1_the5ers`; 15 have a harvest, the other 15 no `harvest/` at all (FileNotFoundError). The 15 with one are refused by the universe builder on the MAE/MFE licence (0.73-0.97 exact, floor 0.99) and reconcile 0.92-0.99 on build and oos1 (e.g. 16425b8a: licence 0.97/0.99, build 0.98, oos1 0.99), so they fail the same way as the golden 4d679e0c (0.44) but closer, which points to the same feed-clock mismatch (archived stamps vs the EETUS bars now behind that feed name) at a smaller scale. `tests/test_portfolio_build.py` is unchanged and still fails; the owner decides whether the equity reconstruction or the archived stamping is what to fix, or whether to archive a fresh strategy after the feeds settle. Items 2 and 4 remain.


## 107. 🟡 Seven tests fail in the 2026-10-07 mechanical audit

Source: `AlgoData/audit/2026-10-07-mechanical.md` (242 run, 227 ok, 7 failed). Not fixed here (documentation pass).

| test | failure | provenance |
|---|---|---|
| `test_ui_batch` | asserts `strategyPermutations/<REAL>/metrics.parquet` (line 194); data gone | 📓 log; cause (10-06 disk cleanup) 🤔 — confirm by checking which cleanup removed it |
| `test_autopilot_closing` | no variants batch with `metrics.parquet, collected.json` for Strategy 10.9.72 | 📓 same 🤔 |
| `test_portfolio_universe` | only check failing: «real fixtures present skipped: files not found» | 📓 same 🤔 |
| `test_mt5_start_check` | reads Tester journal `…/Tester/logs/20260930.log`, no longer on disk | 📓 |
| `test_worker_lifecycle` | stop path runs `python3 -m ui.daemon.loader.afterrun` from a cwd outside the repo → `No module named 'ui'` | 📓; possible real bug in `bin/sqx-worker.sh stop` run from another cwd |
| `test_sqx_live` | `KeyError: 'strategies'` at `sqx/projects/live.py:235` (`listStrategies` reply) | 📓; stub vs contract not diagnosed |
| `test_variants` | shapes/hash dump differs | 📓; not diagnosed |

Fix direction: point the data-dependent tests at a fixture; set cwd/`PYTHONPATH` in `bin/sqx-worker.sh`.

**2026-10-08 (documentation pass).** The 10-08 mechanical audit (`AlgoData/audit/2026-10-08-mechanical.md`: 265 run, 249 ok, 9 failed) repeats these seven and adds three — 📓 from the report, none diagnosed here:

| test | failure |
|---|---|
| `test_batches` | `No module named 'studies'` at line 6 — run without the repo root on `PYTHONPATH` |
| `test_ui_blocks` | `KeyError: 'tabs'` at `tests/test_ui_blocks.py:60`: a block JSON has no `tabs` (test or data drifted; yesterday a shell timeout) |
| `test_feed_from_db` | fixture ranges end the day after the last bar (bars now end 2026-10-0x) and `B.xml` reads timezone `XEETUS` vs registry `EETUS` — time-dependent fixture dates |

`bin/sqx-worker.sh` line 386 already runs `afterrun` inside `cd "$ROOT"`, so the `test_worker_lifecycle` failure 🤔 comes from the test's own call or an uncommitted edit — confirm by rerunning it after the script's change is committed.


## 108. 🟠 Step 12 redesigned (T0-T4, steps 11.5 and 11.7) built beside the old one: waits for the first real run and the owner's «corta»

Encargo 47 (`docs/encargos/47-paso-12-otras-temporalidades-pico-aislado.md`), parts K, F, S, P and D done 2026-10-07 without SQX. The live rule is still `crossTF.combined.z_new`; parts V (validation, the cut) and B (deleting the old reading) wait. Spanish name of the issue: «paso 12 nuevo construido al lado: espera la primera corrida real (parte V) y el corte del dueño».

**Only SQX can verify (part V):**
- the phase-2 tasks `CrossTF <TF> build` run and write their databanks `CrossTF_<TF>_build`;
- whether a re-run task overwrites or appends to its databank;
- periods doubled on M15 (M30 mothers) are accepted by every indicator;
- `k / c` with c < 1 may exceed a block's `maxValue` (PMax 10.99 → 15.6 on M15, per the encargo): does SQX accept it;
- the cost in time of phase 2 (proposal §8.5);
- `z_delta` and `z_build` centred on 0 with real edgeless mothers (proposal §8.7; the synthetic battery is fine);
- `apply_verdict` on `CrossTF_Input` at 11.5 (mother out with her siblings, the others kept);
- a re-run of 11.5 may read a stale `CrossTF_<TF>_build` export.

**Owner decisions pending:**
- K-1: the R of `ret` (each timeframe's own, as implemented, or the mother's via `c`);
- K-2: a lone measured neighbour that fails T2a or T2b (its NO PASA, or LIMBO as implemented);
- K-3: the window of T4 (the mother's bar, as implemented, or the slower of the two);
- `CBlock_CandleBreakoutLong*.Double2` («body > Mult × ATR»): `bar` or a ratio `other` (today `unverified` in `sqx/variants/ranges.yaml`).

## 109. 🟠 mcRetest «Estrategia a estrategia» does not draw: `help` longer than `columns`

Found by the 2026-10-09 audit (`tests/test_ui_blocks.py`). `studies/breakage/mcRetest/many.py:34-35` sets
`strategy_table["help"] = SHOWN_HELP + criteria.HELP[1:4]` (11 entries) whatever the table holds; for
`reports/Test_USDJPY_M30_doubleROCLong_10k/MCR_All/2026-10-08/mcRetest/mcRetest.json` the table has 8 columns,
so `ui/desktop/blocks/table.py:137` gets `horizontalHeaderItem(j) is None` and the window shows «No se pudo dibujar».
Fix: build `help` from the columns actually present (or truncate to `len(columns)`), and make `table.py` skip a missing item.
Also: `raw/<project>/T1_Neighbours/<day>/` (written by `studies/breakage/mcRetest/neighbours/t1.py:126`) carries no `manifest.json`.
Also (audit 2026-10-09): `tools/checks.py` fails on `pipeline/autopilot/run.py` at 256 lines (max 250) after the 10-08 edit — split it; `test_export_manifests` fails its output-folder listing assert while `sqx/export` has uncommitted edits — rerun after the commit.

