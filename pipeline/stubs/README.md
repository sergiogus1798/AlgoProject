# pipeline/stubs — what stands in for a real module during a fixture run

All twelve stages in `recipe.yaml` drive a real module. `placeholder.py` is not filling a gap
anymore: it is kept for `pipeline/verify/`, which swaps every row's `command` for it so the
resumption, progress and monotonic-ledger tests run against a fixture instead of SQX or a real
export — see `pipeline/verify/fixture.py` and `pipeline/verify/selftest.py`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `placeholder.py` | reports progress like a real stage, then writes an invented output shaped like the stage it stands in for | `python3 -m pipeline.stubs.placeholder --stage build --work DIR` | nothing → `<work>/<stage>.json` |

⚠️ **Every number it writes is invented**, and the file it writes says `"placeholder": true` so
nothing downstream can mistake it for a measurement. The `collected` stage additionally writes a
real, tiny export and a real, tiny folder of variants, so the sweep in `pipeline/cleanup.py` is
exercised against something that is actually on disk.

Nothing outside `pipeline/verify/` imports this folder. It stays for as long as the fixture tests
need something to swap the real commands for.
