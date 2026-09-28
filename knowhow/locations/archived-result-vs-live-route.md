---
q: compare source=archive with source=live; archived result differs from live; partials only in live; mcRetest strategy name 10.11.79 without Strategy prefix; /api/result live returns null for mcRetest; crossTF spread per-strategy result null population only; F12 import acceptance diff
tag: 🔬  date: 2026-09-28  see: locations/which-reports-pair-by-identity
---
# An archived result is that day's rendering: diff it against live for that day, under the study's own name
Checking `source=archive` against `source=live` on `/api/result`: ask live with `day=` and
`strategy=` from the manifest's `studies[].day` / `.named` — `mcRetest` names it `10.11.79`, not
`Strategy 10.11.79`, and live answers `result: null` under the databank name (the archive route
is keyed by identity). Keys the store added after archiving (`result.partials`, 2026-09-28) show
only in live: the archive keeps what was served that day. `crossTF` and `spread` hold only a
population result; the strategy's entry is `null` in both.

## Evidence
`Test_USDJPY_donchianUpperCrossUp_M30`, identity `4d679e0c…`, daemon on 8765, 2026-09-28:
version `2026-09-27T2039` → crossTF, spread, tearsheet IS/OOS equal; mcRetest, gate, isOos differ
only by `$.result.partials solo en vivo`. Version `2026-09-28T0724` → every route equal (mcRetest,
gate, isOos, snoopingScreen, spread, crossTF, tearsheet). Live mcRetest with
`strategy=Strategy 10.11.79` → `meta.day: None`; with `strategy=10.11.79` → same hash as archive.
`/api/tearsheet` also differs by `computed_at` when the two calls straddle a second: it is the
request time, not data.
