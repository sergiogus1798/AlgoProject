---
q: builder --only drops tasks wrong input databank; task Input Output databank matched by string; chain_databanks; phantom Results-Rexpect input on build task
tag: 🔬  date: 2026-09-23  see: databanks/, authoring/donor-clone-market
---
# After `builder --only`, rethread each task's Input to the previous task's Output
Task `Input`/`Output` databanks match `config.xml` by string; an undeclared name is silently ignored.
A subset of donor tasks keeps its old pointers and can test an empty databank and pass everything.
`sqx.projects.databanks.chain_databanks` threads them in `config.xml` `<Task>` order;
`builder --json` reports it as `chain` (with what each task read before).

## Evidence
XML: `<Databank label="Input databank" name="Input" value="…">` plus `Output`.
Three-task donor clone: the additional-markets task read `Retest Markets - Family`, its own output.
| task | reads | writes |
|---|---|---|
| Build | — (left alone) | `Results` |
| Retest (OOS) | `Results` | `OOS` |
| Retest (additional markets) | `OOS` | `Retest Markets - Family` |
📓 First task's input left alone: Build on `generationType="genetic-evolution"` seeds from system
databanks (`Initial population`, `Strategies to improve`), not `Input`. Donor ships undeclared
`Results-Rexpect` there; owner's master: `XAUUSD`, `TestXAUUSD2` → `Results-Rexpect`; `USDJPY`,
`EURUSD`, `AUDJPY` → `Retest Markets IS`; `SP500_H1` + five `XAUUSD_Breakout_H1` build tasks → `null`.
Six of eleven point at nothing; builds run (`XAU_ISOOS_ejemplo` produced 120). Owner's config, inert — don't change.
