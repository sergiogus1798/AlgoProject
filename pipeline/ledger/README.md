# pipeline/ledger — the C5 contract, and the only thing that outlives the data

One `state.json` per mother strategy, at `AlgoData/pipeline/<project>/<strategy>/state.json`.
It is the interface with everything else: `perf/disk/retention.py` already reads
`stages.collected.removable` to decide what is provably safe to delete, and the future daemon
serves `stages.<name>.progress` straight to its progress bar.

| file | what it does | run it | in → out |
|---|---|---|---|
| `state.py` | reads and replaces the ledger, atomically | imported | work directory ↔ `state.json` |
| `progress.py` | records how far a running stage has got, while it runs | imported | percentage and status → ledger |

## The contract

```json
{ "strategy": "Strategy 17.9.39", "stage": "collected",
  "stages": {
    "sppultra": {"done_at": "...", "progress": 100, "status": "8.412 permutaciones leídas",
                 "verdict": "proceed", "n_eff": 3381, "brief_hash": "d081df20…"},
    "build":    {"started_at": "...", "progress": 37, "status": "1.850 de 5.000 escritas"} },
  "costs_provisional": true }
```

Everything past `progress` and `status` is lifted from the stage's own output by the `record` and
`hash` fields of its recipe row — the ledger never computes a figure of its own.

**`brief_hash` is not decoration.** It names *which* design the later stages were built from, and
`gates.unchanged` refuses to continue when the brief on disk no longer hashes to it. A brief edited
after the variants were fabricated is the failure mode that produces plausible results instead of
an error: 5,000 variants of one design, judged against the numbers of another.

- **`progress` is monotonic inside a stage.** It never goes back, and a stage that reports a lower
  value raises rather than being clamped. A bar that slides backwards is indistinguishable from a
  pipeline repeating work it had already done, so the contract is only worth having if breaking it
  fails loudly. `pipeline/verify/monotonic.py` is what turns that sentence into a test.
- **It is written during the stage, not at its end.**
- **A write cannot corrupt the file.** Temporary file plus `os.replace`, which is atomic on the
  same filesystem. This is the one place in the module that guards against something going wrong,
  and CODESTYLE's "no defensive code" does not cover it: another process reads this file while a
  stage writes it, and surviving a kill mid-write is a stated requirement, not a guess about bad
  input.
- **Another process reads it while you write.** A liveness monitor today, a daemon tomorrow.

## `costs_provisional`

Stamped when it is opened, from `assets/<asset>.yaml`: true while any required cost override still
says PROVISIONAL. Every report built on the run inherits it, so a number produced with SQX's
default spread can never later be mistaken for one produced with the broker's real figures.
