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
| `banks.py` | The custodian's four variant databanks, emptied off the disk between two batches. | imported | project → files deleted |
| `collect.py` | Join the three legs' metrics onto the manifest and write contract C3, metrics.parquet. | `python3 -m sqx.variants.collect --work <dir>` | csv + parquet → `metrics.parquet` |
| `curves.py` | Every variant's cumulative curve off one leg's databank, checked against what SQX stored. | imported by `equity.py` | databank folder → curves |
| `equity.py` | Harvest every variant's per-day P&L from the three legs, per market, and join them. | `python3 -m sqx.variants.equity --work <dir>` | `.sqx` → `equity.parquet` |
| `execute.py` | Retest a fabricated batch on the custodian and read the IS/OOS panel back out. | `python3 -m sqx.variants.execute --work <dir> --project <SYM>_variantes`; `--clear` empties the four databanks between batches | `.sqx` → `retest.csv` |
| `harness.py` | Rewrite one already-configured task -- SPP IS, SPP OOS or OOS -- from a donor known to run. | `python3 -m sqx.variants.harness --kind spp_is --project Trade_XAUUSD --output SPPRecon_Out …` | donor task → the worker's `project.cfx` |
| `inputs.py` | What the factory reads: its own settings, the design brief, the known results, where it writes. | imported | names → values, paths |
| `legs.py` | The three legs of the WFC/CSCV retest: what each one is called and where its output lands. | imported | doctrine → legs, databank folders |
| `lengths.py` | Which variables of a strategy are lengths in bars: SQX's type, the custom-block table, the name. | imported | portfolio XML → (lengths, unverified) |
| `livexec.py` | `execute`'s load, run, panel, sync and clear on a live GUI session (`sqx.projects.live`), no restart. | imported | a batch folder → the three legs retested, mirrored to disk |
| `make.py` | The command: one design brief in, the .sqx batch and its manifest out. | `python3 -m sqx.variants.make --brief <design_brief.json> --project XAUUSD` | brief → `.sqx` + parquet |
| `manifest.py` | Contract C2: what was fabricated, read back off the disk. Never what the plan meant to fabricate. | imported | folder → parquet |
| `mothertrades.py` | Each batch's mother, trade by trade: her retested `.sqx` kept per leg, exported in one SQX start. | `python3 -m sqx.variants.mothertrades --work <dir> [--work <dir> …]` | `origin/*.sqx` → `trades.parquet` |
| `neighbourbatch.py` | Step 14's T1 batch: every mother and her drawn neighbours as `.sqx`, and their retest on the two legs. | `python3 -m sqx.variants.neighbourbatch --mothers <dir> --out <work>`, then `--work <work> --project <P>` | mothers → `sqx/` + `manifest.parquet`; batch → retested legs + `ran.json` |
| `neighbours.py` | Step 14's T1 draw: which parameters of a mother move, and her neighbours with all of them moved at once. | imported | portfolio XML → tuples, duplicates |
| `pilot.py` | The pilot: fabricate and retest a few hundred sampled tuples before the full batch exists. | `python3 -m sqx.variants.pilot --brief <design_brief.json> --project <SYM>_variantes --out <dir>` | live levels → banned levels + `pilot.json` |
| `ranges.py` | Which coefficients of a strategy multiply a per-bar measure, and the ATR ratio they move by. | imported | portfolio XML → measures; bars → c |
| `rebuild.py` | Write a step-12 scaled sister again from the stored mother and the parameters the store kept. | `python3 -m sqx.variants.rebuild <identity> [H1 …] --out DIR` | store → sibling `.sqx` |
| `scale.py` | Rescale one strategy's bar-unit parameters to another timeframe, as a sibling .sqx. | `python3 -m sqx.variants.scale --mothers <dir> --project P [--source H1] [--targets M30 H4 D1]` | mother → siblings + `scaling.parquet` |
| `tooltips.py` | One sentence per config.yaml knob of the variant factory, for the window's Configuración SQX › WFC. | imported by `ui/daemon/sqxconfig/studies.py` | — |
| `tuples.py` | The canonical form of a parameter tuple and its hash. Both ends of the factory use it. | imported | tuple → hash, columns |
| `united.py` | Per-segment and per-market metrics read off the .sqx, and the exact union of any of them. | imported | `.sqx` → long frame, unions |
| `varianttrades.py` | Every variant's trades on the three legs and every market, in one `variant_trades.parquet` per batch. | `python3 -m sqx.variants.varianttrades --work <dir> --project <P>` | exports → `variant_trades.parquet` |
| `config.yaml` | Every tunable: the seed, `size` (ledger `variants.n_min`, `n_max`, `per_coefficient`), the canaries, the file shape | edited | — |

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
