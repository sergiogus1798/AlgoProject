---
q: edit assets/*.yaml keeping comments, ruamel round-trip byte identical, core.assetyaml, indent width null representer, comment of a key lc.key ca.items, set_value flow list becomes block, quoted "true" loses quotes, remove list item keep comments, emptied list blank line lost, set_market
tag: 🔬  date: 2026-09-27  see: eng/no-slicing-xml-yaml-by-index
---
# Write `assets/*.yaml` through `core.assetyaml` (ruamel round-trip)
ruamel round-trip returns these files byte-identical only with three settings, all in `core/assetyaml.py`:
`indent(mapping=2, sequence=4, offset=2)`, `width=4096`, explicit `None` → `null` representer. Missing any → spurious
diff in all nineteen files. Whole-document read/write keeps blocks others added; only a same-key concurrent change is lost.
(`core.assetwrite` is the single writer — `assets/RULES.md`.)
Replacing a value: a plain Python list turns `[H4, H12]` into a block (3-line diff) — pass a `CommentedSeq`
with `fa.set_flow_style()`; a plain str drops the quotes of `"true"` (then YAML reads a bool) — wrap it in
`type(old)(new)`. `ui/daemon/sqxconfig/write.py` does both. Rows of a list: edit in place, never reassign (comments go).

## Evidence
- Without indent: every list dedents; without width: long `why` lines split; default None writes empty (`min:` alone doesn't read as "undecided").
- Cosmetic losses: a hand-wrapped multi-line scalar (EURUSD `notes:`) comes back on one line; column padding inside flow maps
  (`{title: WFC 1 IS,   segment: build}`) normalised to one space. No comment touched.
- Emptying a list eats the blank line after it: the lines after a block list's last item live in `seq.ca.end`,
  and an empty seq is not emitted with them. 🔬 2026-09-27 fix (`assetwrite.set_market`): make it flow and move
  the tokens to the parent key's eol slot, `parent.ca.items[key] = [None, None, tok, None]` with
  `tok.value = "\n" + joined` → add-then-remove of a row is a zero diff.
- 🔬 2026-09-27: `set_value('build', ['crosstf','timeframes','H1'], ['H4','D1'])` → block list; with a flow
  `CommentedSeq` → `-    H1: [H4, H12]` / `+    H1: [H4, D1]`, one line. `ExitOnFriday: "false"` kept quoted.
- 📓 `read()` loads the whole doc, `write()` emits it whole → another session's added block survives.
- `lc.key(k)` gives each key's line in a `CommentedMap`; read the comment above/beside from the text. `ca.items` hangs a key's comment
  on the PREVIOUS key (sometimes another level's). This lets the window explain each field in the file's own words.
