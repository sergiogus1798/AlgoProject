# sqx/variants — the variant factory

Stage 2 of the robustness protocol. A design brief comes in; **N `.sqx` files and the manifest that
says what each one is** go out. `execute.py` then loads the batch into the custodian and retests it,
`collect.py` writes the metrics panel, and `equity.py` keeps the one thing that panel throws away:
what each variant earned **day by day**.

That last one is what makes the CSCV possible. A databank export gives 41 aggregate numbers per
variant and no way to re-cut the windows; the retested `.sqx` carries a `dailyEquity.bin` that
`core.sqxstats.equity` reads with no SQX running. Measured 2026-09-22: 962 variants in **1.5 s**,
5.9 MB of Parquet, against roughly 90 minutes to export their trades — a cost step 16.5 now pays once per batch for `variant_trades.parquet` (`varianttrades.py`), because the WFC and the cloud price every variant's own trades.

⚠️ **A retested `.sqx` carries THREE equity curves** -- `Results/Portfolio/`, `Results/Main: …/` and
one per cross-check market -- and `Portfolio` comes first in the archive. Reading whichever appears
first gives gold plus silver where the databank's net profit is gold alone: 10,476 against 35,328 on
`P00000`. The result is named, never taken by position, and `equity.py` checks every curve against
the profit SQX stored at the in-sample boundary before it writes anything.

Why it exists at all: **no `sqcli` verb changes a strategy's parameters.** The only way to score a
chosen combination is to write it into a `.sqx` and retest that file.

```
design_brief.json ─▶ design ─▶ build ─▶ manifest
    contract C1     which       write    what is
                    tuples      the      actually
                                files    on disk
                                         contract C2
```

| folder | the question it answers | read its README before |
|---|---|---|
| `design/` | which combinations, and why those? | changing the hypercube, the box or the batch size |
| `build/` | how does a combination become a file? | touching the `.sqx` rewriting |

| file | what it does | run it | in → out |
|---|---|---|---|
| `make.py` | The command: brief in, batch and manifest out (a Latin hypercube over the plateau, `design/README.md`). Runs the trade-count pilot first (OPEN.md #41), unless `--no-pilot`/`--design-only` or `pilot.enabled: false` | `python3 -m sqx.variants.make --brief <design_brief.json> --project XAUUSD` | brief → `.sqx` + parquet |
| `pilot.py` | A few hundred sampled tuples, fabricated and retested on `--project` before the full batch exists, scored on trade count alone; reuses `execute.awake`/`load`/`run`/`synced`, creates nothing of its own | `python3 -m sqx.variants.pilot --brief <design_brief.json> --project <SYM>_variantes --out <dir>` | live levels → banned levels + `pilot.json` |
| `inputs.py` | Reads `config.yaml`, the brief, the already-known results, and says where output goes | imported | names → values, paths |
| `tuples.py` | The canonical form of a parameter tuple and its hash | imported | tuple → hash, columns |
| `manifest.py` | Contract C2, built by reading the files back off the disk | imported | folder → parquet |
| `livexec.py` | `execute`'s `awake`/`load`/`run`/`panel`/`synced`/`clear` on this holder's live GUI session (`sqx.projects.live`); `backend(cfg)` picks it or `execute`. The legs run by the projectXML of the start, the panel is `loadGridData` (no reader needs it), the clear is `removeReports` + sync | imported | a batch folder → the three legs retested, mirrored to disk |
| `execute.py` | Loads a batch into the custodian, runs the retest harness, exports the panel | `python3 -m sqx.variants.execute --work <dir> --project <SYM>_variantes`; `--clear` empties the four databanks between batches | `.sqx` → `retest.csv` |
| `banks.py` | Empties the input and the three legs' databanks off the custodian's disk, refusing while the install is up; and what `execute.run` reads while it waits — `mark`/`aborted` follow «Error while running project» across every log of the install (midnight included), `in_bank`/`tested` parse an `action=status` reply or name it | imported | project → files deleted |
| `collect.py` | Contract C3: per-segment and per-union metrics joined onto the manifest, plus `segments.parquet`; **drops no variant for trading little** (`usable` is all true; each study applies its own floor); refuses a batch whose controls all returned the same number | `python3 -m sqx.variants.collect --work <dir>` | csv + parquet → `metrics.parquet` |
| `varianttrades.py` | **Every variant's trades** (encargo 48 F): after `collect`, `export_retest --batch variants` has exported the three legs with every market; this reunites them into `variant_trades.parquet` in the batch folder — schema T (`core.tradestore.KEEP`, plus `Symbol`, `block`) with `variant_id`, `leg` (`build`/`oos1`/`oos2`), `market` (`Main` where `Symbol` is the project's own feed, else the feed — never by `block`) — controls included, tagged in the manifest; the per-leg export folders are deleted. `engines/variants/excess.py` reads it | `python3 -m sqx.variants.varianttrades --work <dir> --project <P>` | exports → `variant_trades.parquet` |
| `mothertrades.py` | The mother's own trades (decision E3, owner 2026-10-04: the mother only — **reverted for the batch by encargo 48 F**: every variant's trades now go to `variant_trades.parquet`, ~90 min measured on the reference run; this module still serves step 20's close-to-close oos2 curve of the mother). `collect` calls `keep`, which copies her retested `.sqx` of each leg into `origin/` before the databanks are emptied; `harvest` exports every batch given in **one** `orderstocsv` and writes each batch's `trades.parquet` (schema T, `variant_id` and `segment` in place of `strategy`), which step 20 rebuilds her close-to-close oos2 curve from | `python3 -m sqx.variants.mothertrades --work <dir> [--work <dir> …]` | `origin/*.sqx` → `trades.parquet` |
| `equity.py` | Every variant's **per-day** P&L for the three legs and every cross-check market, joined into one continuous curve | `python3 -m sqx.variants.equity --work <dir>` | `.sqx` → `equity.parquet` |
| `curves.py` | Reads one leg's curves on every core and checks each against the net profit SQX stored, telling an open position at the boundary from a wrong-result read | imported by `equity.py` | databank folder → curves |
| `harness.py` | Rewrites one already-configured task of a project from a donor task that is known to have run: SPP in sample, SPP out of sample, or a plain retest with a cross-market check. The target task is found by **title**, never by file name — `write()` looks up "SPP IS"/"SPP OOS"/"OOS" in `--project`'s own config.xml and touches only that member. `--project` is the mother's own workflow project (hard rule 10, OPEN.md §38) -- it already carries these tasks (`sqx/projects/stages.yaml`, kept from the donor by `sqx.projects.builder --workflow`), so no project is built just to hold the harness | `python3 -m sqx.variants.harness --kind spp_is --project Trade_XAUUSD --output SPPRecon_Out …` | donor task → the worker's `project.cfx` |
| `spp.py` | Runs one mother's SPP reconnaissance on the custodian and leaves the profile where `export_spp` finds it | `python3 -m sqx.variants.spp --work <dir> --mother <sqx> --kind spp_is --chart '…'` | mother → profile + `spp_is.json` |
| `scale.py` | **A different job in the same lane**: one mother's bar-unit parameters rescaled to another timeframe, as sibling `.sqx` plus the manifest of what moved; a faster target (H1→M30) multiplies the periods. Not brief-driven -- read by `studies/transfer/crossTF/`; `fabricate()` is what `sqx.projects.crosstfload` calls at step 10.5 | `python3 -m sqx.variants.scale --mothers <dir> --project P [--source H1] [--targets M30 H4 D1]` | mother → siblings + `scaling.parquet` |
| `rebuild.py` | A step-12 sister's `.sqx` written again from the strategy store: the stored mother scaled with the stored ATR ratio and batch index, then checked against the stored `param_*` and the identity of the file fabricated then (owner, 2026-10-08: the store keeps no sister's file). Skill: `/rebuild-sister` | `python3 -m sqx.variants.rebuild <identity> [H1 …] --out DIR` | store → sibling `.sqx` |
| `lengths.py` | Which variables of a strategy are lengths in bars, for `scale.py` (owner, 2026-10-02: «arregla el escalado»): what SQX itself types `ParamTypePeriod`; for a custom block, the ruling of `lengths.yaml` and nothing else (WAE's `Sensetive` is typed a period and is a multiplier); the name patterns of `config.yaml` only as a fallback (`ExitAfterBars`, files older than the field). `lengths.yaml` rules every custom block of the six v3 palettes parameter by parameter — `length`, `other` or `unverified` (left unscaled, sibling flagged, the study reads it `unusable`) | imported | portfolio XML → (lengths, unverified) |
| `ranges.py` | Which coefficients move with the timeframe, for `scale.py` (encargo 47 part F, owner 2026-10-07): `measures` rules every non-length parameter `bar` / `window` / `other` / `unverified` from `ranges.yaml` (read off each block's formula) and the distance formulas (`ATRBasedValue` is `bar`); `stops` rewrites the literals of an ATR stop or target; `ratio` is c — median ATR on the sibling's timeframe over the mother's — and `measured` computes it over build + oos1 of the bar library (0.7 s, not cached). A `bar` coefficient is written k / c; an `unverified` one flags the sibling | imported | portfolio XML → measures; bars → c |
| `stopgrid.py` | **The stop-loss batch of step 22**: per mother the original without a stop (reference), the `X = 1000` probe that must reproduce it trade for trade, and — with `--grid` — every X of the study's stability grid, grafted by `build/stoploss.py`; then `execute` and `export_retest` as they are | `python3 -m sqx.variants.stopgrid --mothers <dir> --out <work> [--grid stopgrid.csv]` | mothers (+ grid) → `sqx/` + `manifest.parquet` |
| `neighbours.py` | **Step 14's T1 draw** (owner, 2026-10-07): which variables of a mother move — every numeric one SQX gave a `<paramType>`, minus what it types a shift and the names `neighbours.fixed` finds (shifts, selectors) — and her N neighbours with ALL of them moved at once, uniformly within ±`entry_pct` (±`exit_pct` for `ParamTypeExitUsed`); ints rounded and floored, duplicates after rounding dropped and counted, seeded by `neighbours.seed` and the mother's name | imported | portfolio XML → tuples, duplicates |
| `neighbourbatch.py` | **The T1 batch**: every mother (neighbour 0, untouched) and her neighbours in one folder, `M003N0042.sqx`, with the manifest read back off the disk; and its retest on the legs `neighbours.legs` names — build and oos1, never oos2 — through `execute`'s own `awake`/`load`/`run`/`synced`, as the pilot. No design brief | `python3 -m sqx.variants.neighbourbatch --mothers <dir> --out <work>`, then `--work <work> --project <P>` | mothers → `sqx/` + `manifest.parquet`; batch → retested legs + `ran.json` |
| `legs.py` | The three legs of the study — segment, task title and output databank — read from `wfc:` in `assets/_build.yaml` so the project and the harvest cannot disagree | imported | doctrine → legs, databank folders |
| `united.py` | Per-segment, per-market metrics read straight out of the `.sqx`, and the exact union of any set of segments | imported | `.sqx` → long frame, unions |
| `config.yaml` | Every tunable: the seed, `size` (ledger `variants.n_min`, `n_max`, `per_coefficient`), the canaries, the file shape | edited | — |
| `tooltips.py` | One Spanish sentence per knob of `size`, `design` and `canaries`, for the window's Configuración SQX › WFC | imported by `ui/daemon/sqxconfig/studies.py` | — |

## The three boundaries, and why they are three

**design** decides and touches no file. **build** writes and decides nothing. **manifest** reads the
files back and describes what is *there*, not what was meant to be there. That third boundary is not
tidiness: it is the only thing that can detect a file whose contents are not the tuple the plan gave
its identifier, and that failure is silent in every other arrangement.

## The four silent failures this module is shaped around

None of them crash. Each produces a study that looks finished and is wrong.

1. **The collision rename.** SQX can hand a strategy back under a name it chose. So the identifier
   `sqx.variants.collect` actually joins the three legs on is the **file name** — SQX names a
   databank entry after the file, `P00000.sqx` comes back as `P00000` — never `<StrategyName>`,
   which SQX is free to rewrite. The collision suffix SQX appends to a duplicate on reload
   (`P00000(1)`) is stripped first, so a batch loaded twice still joins onto the right row instead
   of silently splitting in two. `sqx.variants.build.rewrite.stamp` also writes a
   `<!--variant_id:P01234-->` comment inside `strategy_Portfolio.xml` at fabrication, but 🔬
   2026-09-26 (issue 43): a retested file comes back **without** it — a retest drops the comment —
   so it is never the join key downstream, only the file name is.
2. **The inherited `<Fingerprint>`.** Every variant is born from one parent and would carry one
   identical fingerprint. If the databank deduplicates on it, five thousand variants become one.
   `rewrite.drop_fingerprint` removes it from every file.
3. **Tuple ≠ file.** The manifest reads the tuple out of the file and hashes it; `manifest.verify`
   compares that against the plan and counts the mismatches. A non-zero count exits non-zero.
4. **The parent's results riding along.** `full` and `no_profile` keep `orders.bin` and the equity
   curve, so a variant that never actually ran shows the parent's numbers and looks fine. The
   manifest cannot see this — the canaries and the databank count can, and `minimal` makes it
   impossible. It is the strongest argument for `minimal` once the install is known to load one.

## The controls

Five rows of every batch are there to fail, not to be analysed:

- **`P00000`, the origin** — the parent rebuilt through the factory. Stratum `origin`, and the
  deletion stage refuses to touch it.
- **three known-result canaries** — real SPP permutations picked at the extremes of the grid
  (highest NetProfit, lowest, fewest trades), carrying the result SQX already stored for that exact
  tuple. Extremes on purpose: a broken chain returns a plausible middling number.
- **one inert pair per frozen parameter** (stratum `inert`) — the origin with a provably dead parameter moved as far
  as it goes. Each must come back equal to the origin, which is the only check on the freezing
  decision itself.

An expectation is on the **in-sample** result and is only meaningful while the retest's in-sample
range is the window the SPP ran on. A retest over different history fails every canary for reasons
that have nothing to do with this module.

## Settled, 2026-09-29

**The file shape is a constant, not an architecture.** Two engineering questions were open on this
install and both came back yes: SQX loads a 5-member `.sqx` with no `orders.bin`, and the databank
does not deduplicate on the inherited fingerprint. All three shapes are implemented; `config.yaml`
picks one. Measured on `Strategy 17.9.39`, 2026-09-21: `minimal` 13.7 KB, `no_profile` 98.7 KB,
`full` 123.3 KB per file — 70 MB, 505 MB and 631 MB for five thousand, fabricated in 6 s, 49 s and
65 s. **The default is `no_profile`** (owner, OPEN.md §23, 2026-09-29): the parent's optimization
profile describes the parent's parameters, so a variant carrying it is carrying a lie, and the owner
chose to pay the extra size for a shape that carries the rest of the parent's own bookkeeping
intact rather than the cheapest one that is merely known not to break.

**The batch size is a cap, never a quota.** A tuple is never repeated to reach it: a plateau with
fewer distinct tuples than `n` gives fewer, and `design.json` says so (`shortfall`).

**Contract C2 carries `canary_expect_same_as`**, approved as a permanent column (owner, OPEN.md §23,
2026-09-29). An inert pair has no absolute expectation — it has to equal another row — and without
somewhere to say which row, the pairs are unusable at collection time. It is null on every other row.
