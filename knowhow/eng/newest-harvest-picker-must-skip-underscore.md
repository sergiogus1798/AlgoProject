---
q: Why did a study crash on _aparte/manifest.json after a re-harvest?
kw: _aparte manifest.json FileNotFoundError, newest folder picker sorted iterdir [-1], re-harvest moves old folder, inputs.py
tag: 🔬  date: 2026-10-09  see: pipeline/monkeyexcess-after-the-cut
---
# A newest-harvest picker must skip names starting with `_`
A re-harvest moves the old folder to `<databank>/_aparte/<day>.<HHMMSS>/`. A picker that takes
`sorted(folder.iterdir())[-1]` picks `_aparte`, because `_` sorts after digits. Skip names starting
with `_`, as `studies/screening/gate/inputs.py` does.

## Evidence
- 🔬 Fixed 2026-10-08 in `studies/data/feedQuality/inputs.py`, `studies/readings/edgeCost/inputs.py`, `studies/screening/maeDepth/inputs.py`.
- Reproduce: `grep -n 'iterdir' studies/*/*/inputs.py`.
