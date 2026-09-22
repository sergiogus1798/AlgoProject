# pipeline/verify — the two proofs that this is a pipeline and not a script

Not golden-file tests, and not in `tests/`: these run the real chain against a throwaway fixture
and assert two properties that are otherwise just good intentions in a README.

| file | what it does | run it | in → out |
|---|---|---|---|
| `selftest.py` | runs both proofs and exits non-zero if either fails | `python3 -m pipeline.verify.selftest` | fixture → problems |
| `fixture.py` | a throwaway mother strategy on disk, so neither proof needs SQX | imported | — → work directory and a design brief |
| `monotonic.py` | progress only goes up, and is written while the stage runs | imported | fixture → problems |
| `resume.py` | a kill mid-stage neither corrupts the ledger nor loses work | imported | fixture → problems |

## What each one actually proves

**`monotonic.py`** reads `state.json` from a second thread while a stage runs — the way a monitor
would — and fails unless it sees at least two distinct intermediate values. Asserting only that
the values never decrease would pass a stage that wrote 0 and then 100 at the very end, which is
the failure the whole design exists to prevent. It also checks that the ledger *refuses* a
backwards write, because monotonicity is only a contract if breaking it raises.

**`resume.py`** starts a stage in its own process group, waits until the ledger reports it partway
through, and `SIGKILL`s the group — not `SIGTERM`, because the claim being tested is that the
ledger survives a machine losing power, not a polite shutdown. It then asserts that `state.json`
still parses, that the killed stage is not recorded as finished, that starting again skips the
stage that had completed, and that the chain finishes.

The fixture lives under `AlgoData/pipeline/_selftest/` and is deleted at the end; `--keep` leaves
it for inspection.
