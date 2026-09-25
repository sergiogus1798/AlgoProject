---
q: databank name with spaces unreachable API, Databank 'Retest' doesn't exist, Retest Markets - Family, MC Trades, load databank with spaces
tag: 🔬  date: 2026-09-23  see: databanks/curating-a-databank
---
# A databank whose name has spaces is unreachable through the HTTP API — use files
The name is cut at the first space (same as `strategies=`); `%20` does not help. Working route: with the
install stopped, copy the `.sqx` into `user/projects/<P>/databanks/<name with spaces>/` and start.
📓 Four of the donor's seven databanks have spaces: `Retest Markets - Family`, `MC Trades`,
`Last generation`, `Initial population` — any API tool loses them silently.

## Evidence
- `-databank action=count project=P name=Retest Markets - Family` → `Error: Databank 'Retest' doesn't exist.`
  `action=load` fails the same.
- File route log: `Loaded 9 strategies to databank Retest Markets - Family`.
