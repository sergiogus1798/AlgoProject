# studies/breakage/mcRetest/neighbours — T1 «especificación»: is the mother a peak or a plateau?

Step 14's T1 (owner, 2026-10-07). Each mother is retested with N parameter neighbours — every
declared parameter moved at once, `sqx/variants/neighbours.py` — over build and oos1, and each
neighbour's trades are priced exactly as step 8 prices them: the common repricer's P/L minus the
calendar-year drift. The facts say how much of the mother's own **excess** her neighbours keep.

It does not go through an MC Retest task: SQX stores only a P/L vector per MC simulation, with no
dates, side or size to compute a drift from (`knowhow/sqx-format/mc-retest-storage.md`).

| file | what it does | run it | in → out |
|---|---|---|---|
| `excess.py` | One window's totals per variant: profit (`engines.market.reprice.real`), the drift collected (`studies.screening.analysis.tradelevel.drift_term`), excess = profit − drift, trades | imported | trades + bars + costs → per-variant totals |
| `t1.py` | `measure` prices a retested batch's exported trades and stores the per-neighbour table; `table` reads one mother's rows back; `facts` gives her T1 facts, or None without a batch; `summary` is the arithmetic | `python3 -m studies.breakage.mcRetest.neighbours.t1 --project <P> --work <batch> --symbol <SYM> --timeframe <TF>` | `raw/<P>/<leg>/<day>/neighbours/trades.parquet` + `manifest.parquet` → `raw/<P>/T1_Neighbours/<day>/neighbours.parquet` |

## What it emits

`facts(project, day, strategy)` returns, for `build` and for `oos1`: `t1.<w>.ret_med`,
`t1.<w>.ret_p5`, `t1.<w>.f_pos`, `t1.<w>.n` (retention of the excess total,
`model/retention.py`), `t1.<w>.ret_benef` (the same median on the profit total: high here and low
on the excess is a false plateau — what holds is the market's drift) and `t1.<w>.beta_share`
(drift the mother collected over her profit); and `t1.rho_vec`, Spearman between the neighbours'
build excess and their oos1 excess; plus two facts for step 16.5's reading (encargo 65 §3d, owner 2026-10-12): `t1.oos1.percentil_madre` (the mother's oos1 excess net of drift as a percentile, 0-100, ties half, among her neighbours) and `t1.dd_r_p99` (p99 of the neighbours' maximum drawdown over build + oos1 together, in R = the doctrine's fixed risk per trade, `gate.market()["risk"]`; `dd_r` is a column of `neighbours.parquet` computed by `excess.drawdowns` with `resample.max_drawdown`; NaN on a table measured before it). They are columns of the «Fragilidad» tab (`mcRetest.fragilidad.t1.oos1.percentil_madre`, `...t1.ambas.dd_r_p99`) — no path yet makes 16.5 read step 14's facts. It judges nothing: the cuts are `pipeline/autopilot/criteria.yaml`'s.

## What it must never hold

- **A threshold.** PASA / NO PASA is the judge's.
- **Its own drift settings.** `drift.window` and `drift.variant` are read from
  `studies/screening/gate/config.yaml`: T1's excess must be step 8's excess, or the retention
  compares two different quantities.
- **oos2.** `SEGMENTS` is build and oos1; the batch's legs are `neighbours.legs` of
  `sqx/variants/config.yaml`, and the autopilot refuses a leg on a reserved segment.

## Traps

- **The mother is neighbour 0 of her own batch**, retested and priced with her neighbours: the
  denominator is never the number another step stored for her at other costs.
- **Identity is the file name** (`M003N0042`), which is what SQX names a databank entry after;
  `(1)` collision suffixes are stripped. A neighbour SQX returned without a trade counts with
  totals of zero (it kept nothing); one a leg never returned (absent from the export's
  `identity.csv`) is left out and counted on stdout.
- **The table is found by day, the newest not after the one asked for**: a batch measured before
  midnight is still the study's the morning after. A second measure on the same day replaces the first.
- **`n` is what was retested, not what was asked for**: draws that round onto the mother or onto
  each other are dropped at fabrication (`duplicates` in the batch's manifest). A mother of few
  small integers has few distinct neighbours, and `t1.<w>.n` says so.
- **Each leg is its own backtest on its own segment at its own costs**, so nothing is split by
  close date here, and a position open at the build's last bar is closed there (`EndTest`).
