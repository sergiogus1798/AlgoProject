# sqx/blocks — custom blocks into an install

| file | what it does | run it | in → out |
|---|---|---|---|
| `install.py` | Add or replace custom blocks in a stopped install's `customBlocks.xml` | `python3 -m sqx.blocks.install <blocks.xml> [--role conductor]` | an XML of `<Item key="CBlock_…">` → the install's store, plus a dated backup |

**No GUI import is needed.** `customBlocks.xml` is the store itself, and `sqcli` never rewrites it
(measured: `knowhow/03-driving-sqx.md`). The GUI does, so the tool refuses to write while the
install's port answers — a write into a running instance is undone on exit, silently.

A key already present is **replaced in place**, never appended a second time: SQX reads the first
match, so a duplicate is invisible until a build picks the wrong one.

The authored XML does not live here. It lives beside the template that needs it, in
`AlgoData/templates/library/<name>/deps/`, so the template folder stays self-contained and installs
on any SQX unchanged.
