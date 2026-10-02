# perf/disk — what the data root costs

Read-only over `~/Desktop/AlgoData`. Nothing here deletes, moves or rewrites anything.

| file | what it does | run it | in → out |
|---|---|---|---|
| `report.py` | runs the four below, appends them, and **exits non-zero when a budget broke** | `python3 -m perf.disk.report` | data root → `disk.csv`, `budgets.csv`, `duplicates.csv`, `formats.csv`, `reclaimable.csv` |
| `budget.py` | each branch against its ceiling from `config.yaml`, the whole root against its own, and the system temp partition (`/tmp`) against `disk.tmp_max_share` | imported | branch rows → verdicts |
| `retention.py` | what could be deleted and how much it would free, by four rules | imported | branch rows → candidates |
| `inventory.py` | one row per branch: bytes, files, formats, days since last write | imported | data root → branch rows |
| `duplicates.py` | files that look like copies of each other, by size and head/tail digest | imported | data root → candidate groups |
| `formats.py` | the same real table as CSV, parquet (snappy and zstd) and feather | imported | sample tables → size and read time |

A duplicate group is a **candidate**, not a verdict: two files matching on size and 64 KB from each
end are almost certainly the same file, but nothing here confirms it and nothing here deletes it.

## Budgets

`report.py` exits non-zero when any branch or the total is over, the same way `perf.catalogue` does
for a regression — which is what lets it sit in cron and be believed. Ceilings live in
`config.yaml` under `disk.budget_gb`, sized 2026-09-21 against 2.3 GB in use with headroom for the
variant study (~200 MB of trades per mother strategy per market, so `raw/` is where growth lands).

The report also prints how full `/tmp` is (`tempfile.gettempdir()`, its own 3.9 GB partition, not under the data
root) and exits non-zero when it is above `disk.tmp_max_share` (0.8) — it filled to 100 % on 2026-09-26 and
broke every shell. Remedy: `bin/weekly-claude-cleanup.sh`. → `knowhow/eng/tmp-partition-fills-with-scratchpads.md`

A branch with **no** budget is reported `unbudgeted`, not passed. A new branch appearing and growing
is exactly what this table exists to make visible, and a default of "unlimited" would hide it.

## Retention — four rules, and only one of them is a verdict

| rule | what it finds | strength |
|---|---|---|
| `collected_variants` | databanks a pipeline ledger records as exported **and hashed** | **a verdict** — the data provably survived |
| `superseded_export` | a dated export whose newer sibling contains every entry it has | candidate |
| `strategy_copies` | `.sqx` files sitting inside exports, duplicating what the databank holds | candidate |
| `intermediates` | `raw/` and `trades/` CSV folders beside a `trades.parquet` that already holds them (exports after 2026-09-23 delete these themselves) | candidate |
| `stale_branch` | nothing written for `disk.stale_days` | weakest — old is not unwanted, and `reports/` accumulates by design |

⚠️ **Nothing in this repository deletes any of it.** These rows attach a number to a decision that
stays the owner's.

🔬 **Why `superseded_export` compares contents and not dates.** Measured 2026-09-21:
`raw/XAUUSD/SPP_IS/2026-09-19` holds only `wfc_pairs/`, while `2026-09-10` holds the full
permutation tables the entire SPP study reads. A newer-date rule proposed deleting the only copy of
the study's input. An older export counts as superseded only when the newer one is a **superset**.

`collected_variants` returns nothing until `pipeline/` exists and has run. An empty list there means
*no evidence*, never *nothing to clean*.
