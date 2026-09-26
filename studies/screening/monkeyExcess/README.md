# screening/monkeyExcess — how many beat their monkeys, and how many should have by chance

| file | what it does | run it | in → out |
|---|---|---|---|
| `report.py` | Over the newest monkey panel of a databank: per statistic, how many pass, how many chance gives, the excess, the share of passes that is luck, and how many survive Benjamini-Hochberg — with every reason to read it warily. A panel of several markets gives one report per market, under `monkeyExcess/<feed>/` | `python3 -m studies.screening.monkeyExcess.report --project XAUUSD --databank Results` | `reports/<P>/<D>/<date>/monkey/nulls.csv` → `monkeyExcess/` |

The excess and the named count answer different questions and routinely disagree: a population can
carry evident signal while none of its members stands out enough to be named.
