# ledger — the global search ledger: what has been tried, and what that costs

Every step of the chain counts its own funnel and forgets it. This module is the book that does
not: **one appended line per search**, over the whole life of a study, so that three survivors out
of ten thousand can be told apart from three out of fifty. That difference *is* the result.

A **search** is anything that looks at data and reduces a population — a build, a retest, a Python
screen, a threshold applied with `/curate`. A **study** is one asset, one timeframe and one template
family: the unit the multiple-testing correction is owed to.

| file | what it does | run it | in → out |
|---|---|---|---|
| `study.py` | What a study is, where its ledger lives, and contract **L1** — the columns of a search | imported | ids → path, frame |
| `record.py` | Builds a row, checks the door, appends it; and the study's funnel | imported | a search → a line |
| `gate.py` | **The one-way door**: who may read a reserved segment, and when 17-19 may be read | imported | step, segment → pass or raise |
| `trials.py` | N and the pooled sigma over every search, the population's n_eff, and the deflated Sharpe that follows | imported | ledger → N, sigma, DSR |
| `spend.py` | The map of spent data: how often each segment has been read, and what is left virgin | imported | ledger → segments |
| `thresholds.py` | **The accessor**: `value(key)` and `fill(cfg)`, which a module's `config()` runs over its parsed `config.yaml` to replace every `ledger:<key>`; and the check of which rows are read through it | imported | register → numbers, divergences |
| `backfill.py` | Rebuilds a study's ledger backwards from artefacts a run already left | `python3 -m ledger.backfill --gate <dir> --symbol XAUUSD --timeframe M30 --family <name>` | a gate report → rows |
| `report.py` | **The command**: the funnel, what was spent, the blind door, and what the whole search costs the Sharpe | `python3 -m ledger.report --study XAUUSD_M30_DirectionalMomentum` | ledger → the panel |
| `thresholds.yaml` | Every threshold of the chain, with who set it and when — **the source**: a module's `config.yaml` holds `ledger:<key>` in its place. Read, never written by code | edited by the owner | — |

Manual page, in Spanish: `docs/manual/43-ledger.md`. Commission: `docs/encargos/8-ledger-global.md`.

## The three things this module exists to get right

**The door is enforced, not trusted.** `gate.allow(step, segment, symbol)` runs *before* the row is
written, reads `assets/_policy.yaml` every call, and raises. 🔬 Step 8 asking for `oos2` on XAUUSD
is refused; step 17 passes. And `gate.allow_read` refuses to serve steps 17, 18 and 19 until all
three have run, which is what makes step 20 blind by construction instead of by discipline.

⚠️ The policy names *tests*, so a step it does not list is refused even where it looks harmless —
the CSCV included. If the CSCV should be allowed to read the reserved stretch, the fix is a line in
`_policy.yaml`, which is the owner's file, not a wider check here.

**The sigma the deflated Sharpe needs is wider than any one batch's.** `trials.accumulated` pools
the moments of every search exactly — `sum n_i(s_i^2 + m_i^2)/N - grand^2` — so no search has to keep
its candidates to be counted later. Today the DSR is fed the spread inside one mother's variants;
that spread is narrower than the study's, always in the direction that flatters the result.

⚠️ **It refuses to pool two units.** SQX stores annualised Sharpes and `core.significance` works per
observation; mixing them yields a plausible number that means nothing. Every row records
`score_unit`, and `accumulated` raises rather than average across two of them.

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
(gate, snoopingScreen, profitShape, entryQuality, cloud, cscv — 14 keys) came out byte-identical on
real data after the move, fingerprint included (`knowhow/eng/thresholds-live-in-the-ledger.md`). A key missing from
the register, or appended twice by two branches, raises on read. `ledger.report
--check-thresholds` says of each row whether its module reads it from here (`ledger`) or still
keeps a copy (`copia`), and fails on a copy that diverges; `tests/test_thresholds.py` swaps every
value for a sentinel and fails if a migrated module does not see it.
