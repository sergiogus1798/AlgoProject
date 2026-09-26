# feedQuality — is the M1 feed fit to judge with, and how much of a strategy's profit sits on its faults

Encargo 17, built 2026-09-26 on the owner's answers to the sixteen decisions
(`docs/AgentPDFs/calidad-del-feed-decisiones-2026-09-26.md`, «Respuestas del dueño») and five
questions of the same day. Two halves, and the second is what justifies the first:

- **Step 4 — describe the feed.** Per feed, independent of any strategy: spikes on the close
  and on the wick in multiples of a trailing hour-of-week scale, which of them revert,
  frozen runs, gaps; counted by year and by month; the stable year and the provider's
  episodes. The preflight (`python3 -m core.assets <SYMBOL>`) prints the warning.
- **Step 8 — attribute.** Per strategy of a gate harvest: which trades touch an anomaly in
  the bar of their signal, entry or exit (or while open, with a stop), and a permutation
  test of whether those trades earn more than chance. Never recomputes a metric without them.

Every number is in `ledger/thresholds.yaml` under `feedQuality.`; `config.yaml` holds
`ledger:<key>` in its place. K and the session of each feed are measured once by
`calibrate` with the owner's criterion and frozen there.

```
inputs ─▶ detect (engines/market/feed) ─▶ calendar ─▶ summary ─▶ feed / scan        step 4
          template ─▶ touch ─▶ alarm ─▶ one / many ─▶ report                       step 8
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.yaml` | Every knob, each a `ledger:` placeholder | — | — |
| `tooltips.py` | One Spanish sentence per knob, for the window's drawer | imported | — |
| `inputs.py` | The knobs, a feed's M1 bars as arrays, its own tick (not SQX's), its frozen session; the harvest, its strategies and trades; a feed's scanned events, refused if scanned under another K | imported | files → arrays, frames |
| `detect.py` | One feed's anomalies under a K and a session: close and wick spikes with their return at m and at the sensitivity m's, frozen runs and gaps in session and apart in the rollover | imported | bars → events |
| `calendar.py` | The library's calendar from Dukascopy's feeds: holidays, partial closes, provider outages; which of a feed's gaps are the whole library's silence | imported | bar minutes → silences, gap classes |
| `summary.py` | Counts by year and month, K*, the stable year and the year grades, the provider's episodes, the residual gaps | imported | events → tables |
| `calibrate.py` | **K\*, session and stable year per feed**, the evidence the ledger rows are written from; proposes, never writes the ledger | `python3 -m studies.data.feedQuality.calibrate` | bar library → `feedQuality/calibration.json` + ledger rows printed |
| `inject.py` | **Synthetic anomalies of known size planted in a copy of each feed** (owner's grid, 2.16): recall, classification, new marks, change of the real count | `python3 -m studies.data.feedQuality.inject [--feed F]` | bar library → `feedQuality/injection.json` |
| `feed.py` | One feed's report as the contract's data | imported | events → result |
| `scan.py` | **Step 4's command**: every feed under its frozen K and session, written for the preflight, the report and INDEX.md | `python3 -m studies.data.feedQuality.scan [--feed F]` | bar library → `feedQuality/<feed>/{events.parquet,summary.json,feedQuality.*}` |
| `template.py` | Where a strategy's .sqx is, and what its rules say: pending entries, live exit orders, a stop — and so which column decides | imported | .sqx → rules |
| `touch.py` | Which trades touch an anomaly in their signal, entry or exit bar, or while open | imported | trades + events → marked trades |
| `alarm.py` | The permutation test on the flagged trades' net P/L and the share of profit at risk | imported | marked trades → p, verdict |
| `one.py` | One strategy's attribution as the contract's data | imported | marked trades → result |
| `many.py` | The population panel and the verdict per strategy (MANTENER, or DESCARTAR only on `action: drop`) | imported | results → panel |
| `report.py` | **Step 8's command**, after `gate.report` on the same harvest | `python3 -m studies.data.feedQuality.report --project P --databank Results --feed F [--strategy S]` | harvest + events → `reports/<P>/<D>/<day>/feedQuality/` + `verdict.csv` |

## Decisions the code carries, and whose they are

- **The tick is the feed's own**, its smallest close-to-close move — not `assets/`'s
  `tick_size`, which for the forex pairs is the pip, ten feed ticks (owner's answer 2.2 says
  «el incremento mínimo de precio del feed»). With SQX's tick the 3-tick floor was 3 pips and
  hid almost every forex spike.
- **The scale changes weekly**: a bar's cell reads the whole weeks before its own week. The
  label depends only on earlier data, as answer 1.3 requires.
- **The session is deduced from the feed** (owner, 2026-09-26): the minutes quoted in at least
  half the weeks of 2015–2019. The forex pairs trade Monday 00:00 to Saturday 00:00; gold and
  silver pause 00:00–01:00 every day, Brent 00:00–03:00 — the same hour all year, because each
  feed is stamped in a zone that moves its clocks with New York's (`knowhow/export/feed-clock-timezones.md`).
  In the weeks the two do not agree (March, late October) the rollover moves an hour: that is
  the March «hueco en rollover» episode gold shows every year.
- **The rollover (23:00–01:59) counts for neither frozen runs nor gaps** (decision 8 and the
  owner, 2026-09-26), and both are **counted apart** in it — `congelado en rollover`, `hueco en
  rollover` — reported and episode-checked, never marked (owner, same day).
- **The stable year's bar is max(3 × median, 30)** (owner, same day): with medians of 2–5 gaps
  a year, one thin Christmas tripled it.
- **The alarm reads IS and OOS together** (owner, same day); the report splits what was flagged
  by sample without a p of its own.
- **The column that decides** is read from the .sqx (answer 3.4): the wick when the strategy
  enters by stop or limit or exits by SL, PT or trailing; the close otherwise. A strategy whose
  .sqx no install holds is `sin .sqx` and not judged.

## What the owner still has to look at

The hand review (`AlgoData/feedQuality/review.csv`): the 20 most extreme close and wick spikes of all 13 feeds, 520 marks — 383 identified real events, 95 unidentified (many at gold's reopening or the rollover), 42 suspect, 38 of them CADJPY's 2006–2008 episode, which fills its whole top 20.

Measured 2026-09-26, in `POSSIBLE_IMPROVEMENTS.md` with the numbers. The injection's «zero new
marks» criterion fails by 1–37 marks per ~12,300 planted in every feed (scale contamination and
MAD discreteness, the ≤ 2 % criterion passes everywhere) — **accepted by the owner the same day**.
Still open: Brent's session is wrong (109 own
gaps a year) and silver's borderline (33); the metals' own holidays read as symbol gaps; a bad
tick's echo is counted as a «movimiento extremo»; and at these K the step-8 alarm is
«insuficiente» for almost every market-entry strategy.
