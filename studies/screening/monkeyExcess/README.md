# screening/monkeyExcess — how many beat their monkeys, and how many should have by chance

| file | what it does | run it | in → out |
|---|---|---|---|
| `report.py` | How many strategies of a databank beat their monkeys, and how many should have by chance. | `python3 -m studies.screening.monkeyExcess.report --project XAUUSD --databank Results` | `reports/<P>/<D>/<date>/monkey/nulls.csv` → `monkeyExcess/` |

The excess and the named count answer different questions and routinely disagree: a population can
carry evident signal while none of its members stands out enough to be named.
