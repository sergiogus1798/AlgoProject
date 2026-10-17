# ledger — the global search ledger: what has been tried, and what that costs

Every step of the chain counts its own funnel and forgets it. This module is the book that does
not: **one appended line per search**, over the whole life of a study, so that three survivors out
of ten thousand can be told apart from three out of fifty. That difference *is* the result.

A **search** is anything that looks at data and reduces a population — a build, a retest, a Python
screen, a threshold applied with `/curate`. A **study** is one asset, one timeframe and one template
family: the unit the multiple-testing correction is owed to.

| file | what it does | run it | in → out |
|---|---|---|---|
| `archived.py` | The study's search count as the archive freezes it beside a strategy's results. | — | — |
| `backfill.py` | Rebuild a study's ledger backwards from the artefacts a run already left on disk. | `python3 -m ledger.backfill --gate <dir> --symbol XAUUSD --timeframe M30 --family <name>` · `python3 -m ledger.backfill --blind <project> --symbol USDJPY --timeframe H1 --family <name>` | a gate report, or WFC/CSCV/WFM results → rows |
| `blind.py` | The rows steps 17, 18 and 19 did not write, rebuilt from the results they left on disk. | imported by `backfill` | results → rows |
| `cells.py` | The per-cell counter: how much was tried in each asset x timeframe x direction x idea family. | imported / `__main__` | project registry, campaign ledger, book, gate funnels → table |
| `gate.py` | The one-way door: who may look at a reserved segment, and when 17-19 may be read. | imported | step, segment → pass or raise |
| `record.py` | Contract L1: one appended line per search that looked at data and reduced a population. | imported | a search → a line |
| `report.py` | The study's whole search, read back: the funnel, what was spent, and what it costs the Sharpe. | `python3 -m ledger.report --study XAUUSD_M30_DirectionalMomentum` | ledger → the panel |
| `shards.py` | Ledger shards (D27, option A): one writer per file, the union read back deduplicated. | — | — |
| `spend.py` | The map of spent data: which stretches of history a search has already looked at. | imported | ledger → segments |
| `steprows.py` | The rows a finished build (step 6) and a WFM reading (step 19) write themselves, live. | called by `ui/daemon/launch/run.py` and `studies/optimisation/wfm/report.py` | log/export → rows |
| `study.py` | What a study is, and where its ledger lives. | imported | ids → path, frame |
| `thresholds.py` | The versioned thresholds, and whether the code still uses the numbers they declare. | imported | register → numbers, divergences |
| `trials.py` | How much was really tried, across every search of a study rather than inside the last one. | imported | ledger (+ extra) → N, sigma, DSR |
| `tried.py` | Contract L2: what a sweep tried, not only what it chose -- one line per value tested. | `python3 -m ledger.tried --study <S> --name <p> --values 1,2,3 --chosen 2 --why "..."` | a sweep → lines |
| `thresholds.yaml` | Every threshold of the chain, with who set it and when — **the source**: a module's `config.yaml` holds `ledger:<key>` in its place. Read, never written by code — except `cscv.blocks`, which the window's Configuración SQX › CSCV writes for the owner, stamping `set_by`, `set_on` and a proposed `why` (2026-09-28) | edited by the owner, by hand or from the window | — |
| `criteria-history.jsonl` | One line per change the window's «Criterios» zone made to `pipeline/autopilot/criteria.yaml` — `at`, `by`, `step`, `what` (añadida, cambiada, borrada, congelado), the rule `before` and `after` — append-only; absent until the first change | written by `ui/daemon/criteria/write.py` | — |

Manual page, in Spanish: `docs/manual/03-datos-costes-y-registro.pdf` (cap. 43-ledger). Tests: `tests/test_ledger_tried.py`, `tests/test_ledger.py`, `tests/test_ledger_ideas.py`.

## Asking whether a cell was tried

`python3 -m ledger.cells --ask <SYMBOL> <TF> [--template T] [--direction D] [--json]` prints the three registries side by side (projects by kind, campaign state, ledger rows and step-8 screenings per segment for the cell, the symbol x timeframe and the whole symbol). The step-8 line reads B from `cells.table()`, not from this printout. Example, `USDJPY M30 --template doubleROCLong` (2026-10-15): 7 `Test_` projects, `oos1` screened 4 times, 30 rows on `oos2`, 58 screenings on `oos1` over the whole symbol. The encargo-62 dossier of 2026-10-11 said 11 `Test_` and 24 `oos2` rows; both differences are explained, not adjustments: the 11 counted projects since retired or renamed (the registry lists only the 7 that still exist under that template), and the 24 predates the `oos2` rows written after 2026-10-12. A `Test_` spends segments, not the cell (owner, 2026-10-14).

## The three things this module exists to get right

**The door binds only an autonomous agent.** Owner, 2026-09-28: a human — at the window, at a
terminal, or steering a session — may read any segment at any time, so `gate.allow` and
`gate.allow_read` return without looking unless `core.assetdata.enforced()` (`ALGO_AUTONOMOUS=1`,
which nothing sets today). Whether an autonomous agent that makes the development decisions should
stay held is left open; the door stays built for it. Under that flag `gate.allow(step, segment,
symbol)` runs *before* the row is written, reads `assets/_policy.yaml` every call, and raises —
🔬 step 8 asking for `oos2` on XAUUSD is refused, step 17 passes — and `gate.allow_read` refuses
17, 18 and 19 until all three have run. Either way the row is written: the ledger keeps counting
every look, which the deflated Sharpe needs whoever looked.

⚠️ **The WFC and the CSCV record their own look; the WFM does it through `steprows.log_wfm`.** Since 2026-09-27
(encargo 24, E1) `studies.optimisation.wfc.report` and `…cscv.report` ask `gate.allow` for every
segment before opening the batch and then write one row per segment read through `record.log`
(`engines/variants/look.py`): the WFC one per segment of its composition (step 17,
`criterion: wfc/<inside>__<outside>`), the CSCV three — `build`, `oos1`, `oos2` (step 18), since its
12,870 partitions cut the whole history. The WFM (19) writes its three rows through `steprows.log_wfm` (called by `wfm.report`); `backfill --blind` rebuilds any missing rows from the results on disk, marked
`backfill`, **skips a batch whose WFC or CSCV already wrote its own** (a live row's note opens
`lote <batch>`), and refuses to write a step twice (`knowhow/pipeline/blind-steps-write-no-ledger-rows.md`).
`BlindJoint` in `STEPS` is step 20's SPA on `oos2` (`studies/closing/blindJoint/`) — the word the
owner would add to `reserved_for`, not a permission.

⚠️ Under `ALGO_AUTONOMOUS=1` the policy names *tests*, so a step it does not list is refused even where it looks harmless.
The CSCV was that case until the owner added it to oos2's `reserved_for` (2026-09-27, Q11: the CSCV
has to see build+oos1+oos2). The fix for the next one is the same: a line in `_policy.yaml`, which
is the owner's file, never a wider check here.

**The sigma the deflated Sharpe needs is wider than any one batch's.** `trials.accumulated` pools
the moments of every search exactly — `sum n_i(s_i^2 + m_i^2)/N - grand^2` — so no search has to keep
its candidates to be counted later. Today the DSR is fed the spread inside one mother's variants;
that spread is narrower than the study's, always in the direction that flatters the result.

⚠️ **Only Sharpes are pooled into sigma.** SQX stores annualised Sharpes and `core.significance`
works per observation. Every row records `score_unit`: `per_period` and `annualised` rows are
pooled (annualised divided by √252, so `sigma` and `unit` are always per period), and any other unit
(`p_pass`, `ev_bank_usd`) adds its `n_scored` to N — they are looks — but never reaches sigma.

**The ideas spent count too, and only the command knows about them** (owner, 2026-10-02). The
hypotheses the ideaExpert measured before any search existed are trials of the study: `report.py`
asks `studies.research.memory.trials.spent` and passes the number to `accumulated(frame, extra)`.
`trials.py` imports no study — the count arrives as an argument — so the dependency runs
command → memory and never inference → memory; the window's ledger view and `core.archive` still
call `accumulated(frame)` and show the searches alone. The market profile's own measures are
printed beside it and **not** added (`knowhow/research/ideas-are-ledger-trials.md`).

**A reconstructed row is weaker than a recorded one, and says so.** `backfill` can only recover what
an artefact wrote down — a funnel knows what it counted, not what else was tried and discarded — so
every row it produces is marked `backfill` and carries the report's own date, not today's.

## Two traps already met

**A soft screen removes nobody.** The gate's `familia` row reports how many it would have kept
(0 of 45 on the example study) while removing none. Recorded literally, the ledger would say the
study ended with nothing left. `backfill` records `n_out = n_in` for a soft screen and puts the
informative count in the note.

**`thresholds.yaml` is the source, reached through one accessor.** A migrated module's
`config.yaml` holds `ledger:<key>` where the number was, and its `config()` runs
`thresholds.fill` over the parsed file *before* any `--set` override, so an override is still held
to the number's type and the window's drawer still shows the knob. The placeholder keeps the key in
its place: the gate prints a screen's thresholds in row order. 🔬 All six modules that declare one
(gate, entryQuality, cloud, cscv — measured when six modules carried one) came out byte-identical on
real data after the move, fingerprint included (`knowhow/pipeline/thresholds-live-in-the-ledger.md`). A key missing from
the register, or appended twice by two branches, raises on read. `ledger.report
--check-thresholds` says of each row whether its module reads it from here (`ledger`) or still
keeps a copy (`copia`), and fails on a copy that diverges; `tests/test_thresholds.py` swaps every
value for a sentinel and fails if a migrated module does not see it.
