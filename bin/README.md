# bin — launchers, workers and scheduled jobs

Shell scripts only. Each starts with a header comment saying what it does; the schedules below are the
ones in the machine's crontab (times are the machine's local time). Scheduled jobs write logs and reports to
the data root, not into the repo.

## Workers and workflow

| script | what it does |
|---|---|
| `workflow.sh` | The whole workflow of one project, steps 5/6 to 25, in one command: `simple`, `template`, `run`, `plan`. Every choice is an argument; the first failure ends it |
| `sqx-worker.sh` | Start, stop, check, sync or run one command on a headless SQX worker (`conductor` or `custodian`), syncing bars first and holding an owner lock |
| `sqx-lock.sh` | The lock library behind `sqx-worker.sh`: one `OWNER` file per install, refuses a second holder |
| `clone-sqx-worker.sh` | Clone the SQX master into a headless worker of a given role (both closed; refuses if it exists) |
| `sqx-log-prune.sh` | Cap the size of SQX's own log directories (archives first). Cron daily 04:15 |
| `weekly-data-update.sh` | The GUI's "Update all" on the master, then refresh asset data ranges and broker commissions, then `mirror-data.sh`. Cron Saturday 02:00 |
| `mirror-data.sh` | Copy the master's `user/data` to the master of every server under `mirrors:` in `machine.yaml` (gorilla). Refuses while SQX runs at either end. Called by the weekly update; by hand after adding a feed |
| `remote.sh`, `remote-check.sh` | Run a command in another server's clone (`mirrors:`, gorilla) after `git pull` there; `--detach` for a workflow. The only door for running code on gorilla: a failed pull runs nothing, and it never pulls under a running SQX or a running workflow (exit 96). After a push, run `bin/remote-check.sh [range]` — checks and tests of the pushed files on gorilla |
| `monthly-oos2-roll.sh` | Move each decided `oos2` window in `assets/_policy.yaml` to the end of the previous month. Cron Saturday 02:05; acts only when due |
| `weekly-reconcile.sh` | Live accounts against the SQX backtest of the same strategies, for the ISO week just ended. Written, not in the crontab |

## The apps

| script | what it does |
|---|---|
| `algoui` | Open the desktop window (`ui/`); `algoui.cmd` is the Windows equivalent |
| `metatracker` | Open the MetaTrader 5 fleet window (a separate app, reads the data root's `fleet/`) |
| `fleet-collect.sh` | Pull the VPS's fleet beacon files into the data root. Cron every minute |

## Scheduled agents (call an LLM, `claude` CLI, unattended)

All source `lib-agent-alert.sh`, which writes an `ERROR-<job>-<date>.txt` and sends a desktop notification
when a run fails or leaves no report.

| script | when | what it does |
|---|---|---|
| `nightly-audit.sh` | daily 03:00 | Daily audit of the repo and data root |
| `nightly-docs.sh` | daily 03:30 | Documenter agent, after the audit |
| `nightly-fix.sh` | daily 04:00 | Fixer agent (Sonnet), last of the nightly chain |
| `nightly-commit-proposal.sh` | daily 05:45 | Proposes a commit; can never commit |
| `daily-funding-deals.sh` | daily 10:00 | Prop-firm discount hunt |
| `daily-literature-scout.sh` | daily 07:00 | Published trading research into the literature file |
| `weekly-knowhow-review.sh` | Sunday 05:00 | Documenter audit of `knowhow/` |
| `weekly-docs-health.sh` | Sunday 05:10 | Documenter audit of `docs/` and `OPEN.md` |
| `weekly-funding-refresh.sh` | Sunday 06:30 | Refresh prop-firm rules and prices |
| `weekly-project-cleanup.sh` | Monday 02:50 | Sweep forgotten `Test_` SQX projects |
| `lib-agent-alert.sh` | sourced | Failure alerting shared by the above |

## Scheduled jobs (no model)

| script | when | what it does |
|---|---|---|
| `audit-prune.sh` | Sunday 02:45 | Gzip old daily audit reports |
| `weekly-claude-cleanup.sh` | daily 23:30 (name is historical) | Delete old session scratchpads in `/tmp` and the data root's `tmp/` |

`sqx-log-prune.sh`, `weekly-data-update.sh`, `monthly-oos2-roll.sh` and `fleet-collect.sh` above are also model-free.
The crontab also runs Python and tool jobs directly (log archive, disk report, dependency map, graphify).

## Install helpers (run once per machine)

| script | what it does |
|---|---|
| `mt5-wine-system.sh` | Root half of MetaQuotes' `mt5linux.sh` (Wine system packages) |
| `mt5-install.sh` | User half: Wine prefix, WebView2, the MetaTrader 5 terminal |
| `sqx-lab-install.sh` | Install and refresh the vendor's sqx-lab toolkit without `/plugin` |

Setup order for a new machine: [`../docs/SETUP-NEW-MACHINE.md`](../docs/SETUP-NEW-MACHINE.md).
