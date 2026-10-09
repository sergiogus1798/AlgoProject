# screening/batches — can several builds of one cell be added up as one big build?

| file | what it does | run it | in → out |
|---|---|---|---|
| `measure.py` | The maths: each strategy's island and the first rule that killed it, the setup fingerprint, the island-by-destination table, the between-batch chi-square judged by relabelling whole islands, each rule's kill rate per batch, the identities a batch repeats from the earlier ones, and the one-line decision | imported | the gate's `verdict.csv`, `funnel.csv`, manifest → dicts |
| `report.py` | The command: reads the newest gate report of each project named, oldest batch first, and prints SUMAR, AVISO, PARAR CELDA or NO SUMAR with the tables behind it. Exit 1 on PARAR CELDA and NO SUMAR | `python3 -m studies.screening.batches.report Test_USDJPY_M30_doubleROCLong_10k Test_USDJPY_M30_doubleROCLong_10k_L2` | `reports/<P>/Results/<day>/gate/` of each → `reports/<last P>/Results/<day>/batches/batches.md`, `.json` |

A machine that cannot build 100,000 strategies at once builds ten batches of 10,000. They are one
population only when the setup is identical (template, feed, segments, the gate's rules), the
funnels do not differ more than chance, and a batch does not regenerate the earlier ones.

**Chance is measured on islands, never on strategies.** The build is genetic: SQX names a strategy
`Strategy <island>.<generation>.<n>`, and an island evolves its own relatives. In the first
10,000 of doubleROCLong · USDJPY · M30, 19 of the 56 survivors came from one island of 20, and the
islands of that one batch spread 38 times what independent draws would. A binomial test would call
any two honest batches different. → `knowhow/research/genetic-build-islands-are-the-sampling-unit.md`

What it does not see: an error common to every batch, and near twins (period 14 against 15 are two
identities). It does not speak the study contract and the window does not paint it: it is a
bookkeeping check between runs, not a reading of a databank.
