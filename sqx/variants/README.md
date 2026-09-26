# sqx/variants — the variant factory

Stage 2 of the robustness protocol. A design brief comes in; **N `.sqx` files and the manifest that
says what each one is** go out. `execute.py` then loads the batch into the custodian and retests it,
`collect.py` writes the metrics panel, and `equity.py` keeps the one thing that panel throws away:
what each variant earned **day by day**.

That last one is what makes the CSCV possible. A databank export gives 41 aggregate numbers per
variant and no way to re-cut the windows; the retested `.sqx` carries a `dailyEquity.bin` that
`core.sqxstats.equity` reads with no SQX running. Measured 2026-09-22: 962 variants in **1.5 s**,
5.9 MB of Parquet, against roughly 90 minutes to export their trades.

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
                    5,000       the      actually
                    tuples      files    on disk
                                         contract C2
```

| folder | the question it answers | read its README before |
|---|---|---|
| `design/` | which combinations, and why those? | changing a stratum or how levels are allocated |
| `build/` | how does a combination become a file? | touching the `.sqx` rewriting |

| file | what it does | run it | in → out |
|---|---|---|---|
| `make.py` | The command: brief in, batch and manifest out | `python3 -m sqx.variants.make --brief <design_brief.json> --project XAUUSD` | brief → `.sqx` + parquet |
| `inputs.py` | Reads `config.yaml`, the brief, the already-known results, and says where output goes | imported | names → values, paths |
| `tuples.py` | The canonical form of a parameter tuple and its hash | imported | tuple → hash, columns |
| `manifest.py` | Contract C2, built by reading the files back off the disk | imported | folder → parquet |
| `execute.py` | Loads a batch into the custodian, runs the retest harness, exports the panel | `python3 -m sqx.variants.execute --work <dir> --project <SYM>_variantes`; `--clear` empties the four databanks between batches | `.sqx` → `retest.csv` |
| `banks.py` | Empties the input and the three legs' databanks off the custodian's disk, refusing while the install is up | imported | project → files deleted |
| `collect.py` | Contract C3: per-segment and per-union metrics joined onto the manifest, plus `segments.parquet`; refuses a batch whose controls all returned the same number | `python3 -m sqx.variants.collect --work <dir>` | csv + parquet → `metrics.parquet` |
| `equity.py` | Every variant's **per-day** P&L for the three legs and every cross-check market, joined into one continuous curve | `python3 -m sqx.variants.equity --work <dir>` | `.sqx` → `equity.parquet` |
| `harness.py` | Rebuilds the worker's one-task harness from a donor task that is known to have run: SPP in sample, SPP out of sample, or a plain retest with a cross-market check | `python3 -m sqx.variants.harness --kind spp_is --project Retester --output SPPOut …` | donor task → the worker's `project.cfx` |
| `spp.py` | Runs one mother's SPP reconnaissance on the custodian and leaves the profile where `export_spp` finds it | `python3 -m sqx.variants.spp --work <dir> --mother <sqx> --kind spp_is --chart '…'` | mother → profile + `spp_is.json` |
| `scale.py` | **A different job in the same lane**: one mother's bar-unit parameters rescaled to another timeframe, as sibling `.sqx` plus the manifest of what moved. Not brief-driven -- read by `studies/transfer/crossTF/` | `python3 -m sqx.variants.scale --mothers <dir> --out <dir> --targets H4` | mother → siblings + `scaling.parquet` |
| `stopgrid.py` | **The stop-loss batch of step 22**: per mother the original without a stop (reference), the `X = 1000` probe that must reproduce it trade for trade, and — with `--grid` — every X of the study's stability grid, grafted by `build/stoploss.py`; then `execute` and `export_retest` as they are | `python3 -m sqx.variants.stopgrid --mothers <dir> --out <work> [--grid stopgrid.csv]` | mothers (+ grid) → `sqx/` + `manifest.parquet` |
| `legs.py` | The three legs of the study — segment, task title and output databank — read from `wfc:` in `assets/_build.yaml` so the project and the harvest cannot disagree | imported | doctrine → legs, databank folders |
| `united.py` | Per-segment, per-market metrics read straight out of the `.sqx`, and the exact union of any set of segments | imported | `.sqx` → long frame, unions |
| `config.yaml` | Every tunable: the seed, the strata knobs, the canaries, the file shape | edited | — |

## The three boundaries, and why they are three

**design** decides and touches no file. **build** writes and decides nothing. **manifest** reads the
files back and describes what is *there*, not what was meant to be there. That third boundary is not
tidiness: it is the only thing that can detect a file whose contents are not the tuple the plan gave
its identifier, and that failure is silent in every other arrangement.

## The four silent failures this module is shaped around

None of them crash. Each produces a study that looks finished and is wrong.

1. **The collision rename.** SQX can hand a strategy back under a name it chose. So the identifier is
   stamped **inside** `strategy_Portfolio.xml` as `<!--variant_id:P01234-->`; the external name is a
   convenience and `sqx_name` records it separately.
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
- **one inert pair per frozen parameter** — the origin with a provably dead parameter moved as far
  as it goes. Each must come back equal to the origin, which is the only check on the freezing
  decision itself.

An expectation is on the **in-sample** result and is only meaningful while the retest's in-sample
range is the window the SPP ran on. A retest over different history fails every canary for reasons
that have nothing to do with this module.

## Open, and deliberate

**The file shape is a constant, not an architecture.** Two questions are unanswered on this install:
whether SQX loads a 5-member `.sqx` with no `orders.bin`, and whether the databank deduplicates on
the inherited fingerprint. All three shapes are implemented; `config.yaml` picks one. Measured on
`Strategy 17.9.39`, 2026-09-21: `minimal` 13.7 KB, `no_profile` 98.7 KB, `full` 123.3 KB per file —
70 MB, 505 MB and 631 MB for five thousand, fabricated in 6 s, 49 s and 65 s. The default is
`no_profile`, which is also the correct one regardless of size: the parent's optimization profile
describes the parent's parameters, so a variant carrying it is carrying a lie.

**`n_target` is a cap, never a quota.** A tuple is never repeated to reach it. `Strategy 17.9.39`'s
brief spans 3,888 live tuples against a target of 5,000, so the coarse factorial is the complete
grid and the remainder goes to coverage, which is the stratum that also varies the frozen parameters.

**Contract C2 carries one column the protocol's table does not list**, `canary_expect_same_as`. An
inert pair has no absolute expectation — it has to equal another row — and without somewhere to say
which row, the pairs are unusable at collection time. It is null on every other row.
