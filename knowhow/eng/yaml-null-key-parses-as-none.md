---
q: Why does cfg["null"] raise KeyError after loading a config.yaml that has a null: section?
kw: KeyError 'null'; YAML key null becomes None; safe_load null key; config section named null; yes no on off keys
tag: 🔬  date: 2026-10-14  see: eng/windows-portability
---
# A YAML key spelled `null:` loads as the Python key None — never name a config section null (or yes/no/on/off)
- `safe_load("null:\n  a: 1")` is `{None: {"a": 1}}`, so `cfg["null"]` is a KeyError. Seasonality named its section `shuffle:` for this.

## Evidence
`python3 -c 'import yaml; print(yaml.safe_load("null:\n  a: 1"))'` → `{None: {'a': 1}}`.
