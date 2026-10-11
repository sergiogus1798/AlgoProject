---
q: Why did step 22 (conditionalMap) die with IndexError on a mother the cosecha does hold?
kw: IndexError index 0 is out of bounds; metrics.index[metrics["strategy"] == strategy][0]; Strategy 1.16.441(1); respelt after retest; closing.reading; identity.spelt
tag: 🔬  date: 2026-10-09  see: pipeline/monkeyexcess-after-the-cut
---
# A mother's name is her last databank's; a study on the panel's cosecha needs the cosecha's name
The autopilot's mothers (`survivors.mothers`) are named as the databank they survive in spells them, and
a retest respells a strategy («Strategy 1.16.441(1)»). Steps 21-22 run one study per mother on the
databank the owner named (`--panel 22=Results`), whose cosecha knows her as «Strategy 1.16.441»: the
name never matched and `conditionalMap.inputs.identity_of` raised a bare IndexError. Since 2026-10-09
`closing.reading` asks `core.study.identity.spelt` for the cosecha's own name of each mother's identity,
and keeps her name where no cosecha paired the databank (step 21 on `CrossTF_Mothers`, an export).
Any new per-mother study on a harvested databank must go through the identity, never the name.

## Evidence
- 🔬 `AlgoData/autopilot/Test_NIKKEI225_M30_simpleL_val/20261005-013319/fallo.md` (step 22) and its `resumen.md`: mothers listed as `Strategy 1.16.441(1)`…; `harvest/Test_NIKKEI225_M30_simpleL_val/*/2026-10-05/metrics.parquet` holds `Strategy 1.16.441` in both `strategy` and `strategy_build`.
- 🔬 `tests/test_identity.py` (`variants_cosecha`): `closing.reading` asks for the cosecha's name.
