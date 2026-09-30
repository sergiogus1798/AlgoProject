---
q: Exceso sobre el mono necesita panel del mono de toda la poblacion siempre; monkeyExcess refuses on the build databank even after monkey ran; monkey panel filed under OOS never Results; SAMPLED set table.py
tag: 🔬  date: 2026-09-29  see: eng/feed-in-config-yaml
---
# `monkeyExcess` reads the OOS databank's monkey panel; it must join `SAMPLED`, not just `monkey`
`studies.readings.monkey` only ever writes its `nulls.csv` on OOS1 or an additional market
(owner, 2026-09-29: never the build a strategy was selected on — `additional_only()` refuses IST
on the project's own market). `monkeyExcess`'s own refusal check
(`DATA/reports/<project>/<databank>/*/monkey/nulls.csv`) reads whichever databank it was asked
for — the build databank ("Results") in the Cribado tab the window shows it in. It therefore
always answered «necesita el panel del mono de toda la población», however many times `monkey`
had already been run on the OOS pair (feedback 2026-09-29 §1.4).

## Evidence
`monkey`, `profitShape`, `entryQuality` and `exposure` already carry this exact shape — a
build-only export has no OOS1 trades — and `ui.daemon.runner.table.SAMPLED` already redirects
them to `find.oos_partner()` before their command is built. `monkeyExcess` was missing from that
set even though its dependency is the same OOS/build split; adding it there is the whole fix,
since `oos1(c)` on the build databank is False regardless of which study asks, and the redirect
then makes `monkey_excess()`'s own folder check look in the OOS databank where the panel
actually lives. No change to `studies/screening/monkeyExcess/report.py` was needed.
