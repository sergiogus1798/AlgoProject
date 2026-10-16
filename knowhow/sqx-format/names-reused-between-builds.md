---
q: Can I pair a strategy across builds or databanks of one project by its name?
kw: same name two identities, variable inlined by retest, Shift variable written as literal, alias-diff.txt, name reused, 529 names 2 identities, pair by name wrong strategy, identity.csv, lineage.csv
tag: 🔬  date: 2026-10-11  see: sqx-format/identity-differs-across-databanks, sqx-format/strategy-identity
---
# Strategy names are reused between builds of one project — pair by identity, never by name
SQX numbers strategies from the start on every build, so a project built twice holds the same
names for different strategies. Pair by identity, or through an export's `identity.csv` /
`lineage.csv`; a name that carries two identities in one databank pairs nothing.

🔬 2026-10-11: the screening harvest paired by NAME until today (`studies/screening/gate/pairing.py`). Now by identity: `alias` = same name, different identity, never paired; `alias > 0` stops the harvest and is written in `manifest.json`. Same pairs as before on four real projects (10, 10, 3, 3), so the change cost nothing there. 🔬 2026-10-16: the retest also writes a variable back as its literal (Shift `VortexShift1` → `1`, its `<variable>` gone; 24 and 5 of 10,000 on USDJPY H1): `pairing.pair` pairs an alias whose definitions match with every variable inlined.

## Evidence
`Test_USDJPY_M30_doubleROCLong_10k`: 529 names carried 2 identities (2026-10-06).
