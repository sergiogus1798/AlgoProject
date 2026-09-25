---
q: edit assets/*.yaml keeping comments, ruamel round-trip byte identical, core.assetyaml, indent width null representer, comment of a key lc.key ca.items
tag: 🔬  date: 2026-09-24  see: eng/no-slicing-xml-yaml-by-index
---
# Write `assets/*.yaml` through `core.assetyaml` (ruamel round-trip)
ruamel round-trip returns these files byte-identical only with three settings, all in `core/assetyaml.py`:
`indent(mapping=2, sequence=4, offset=2)`, `width=4096`, explicit `None` → `null` representer. Missing any → spurious
diff in all nineteen files. Whole-document read/write keeps blocks others added; only a same-key concurrent change is lost.
(`core.assetwrite` is the single writer — `assets/RULES.md`.)

## Evidence
- Without indent: every list dedents; without width: long `why` lines split; default None writes empty (`min:` alone doesn't read as "undecided").
- Cosmetic losses: a hand-wrapped multi-line scalar (EURUSD `notes:`) comes back on one line; column padding inside flow maps
  (`{title: WFC 1 IS,   segment: build}`) normalised to one space. No comment touched.
- Emptying a list eats the blank line after it.
- 📓 `read()` loads the whole doc, `write()` emits it whole → another session's added block survives.
- `lc.key(k)` gives each key's line in a `CommentedMap`; read the comment above/beside from the text. `ca.items` hangs a key's comment
  on the PREVIOUS key (sometimes another level's). This lets the window explain each field in the file's own words.
