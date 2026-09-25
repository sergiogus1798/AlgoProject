## AlgoProject — read this first. Where it differs from the vendor text below, this wins.

Usually reached from `sqx-strategy-template` when the condition the owner described does not
exist yet. Nothing here starts SQX.

**1 · Ask the logic, always** (CLAUDE.md hard rule 11): which line, state or transition, which
price, which shift. List the readings and ask; never pick the common one.

**2 · Exactly what he said.** Check first with `python3 -m sqx.inspect.vocabulary <term>` (repo
root). If the exact logic is missing, author it — never approximate it with the nearest block.
What he named is fixed; periods and deviations he did not name are exposed params, optimizable.
Author the opposite block too and point `oppositeBlockKey` at it: every block on this install has
one, and a dangling key breaks a mirror silently.

**3 · Where the XML goes.** Into the template's library folder,
`~/Desktop/AlgoData/templates/library/<name>/deps/blocks.xml`, not only `engine/out/`.

**4 · Install it on both workers, stopped, never the master** (hard rule 3: `ListAgents`,
`ls -lt <worker>/user/projects | head`, the log). The vendor's "import into AlgoWizard" does not
apply — the owner rarely opens the GUI:

```bash
python3 -m sqx.blocks.install <deps/blocks.xml> --role conductor
python3 -m sqx.blocks.install <deps/blocks.xml> --role custodian
python3 -m sqx.inspect.vocabulary --diff custodian     # must report no gap
bin/sqx-lab-install.sh                                 # rebuild the catalogs
```

The catalogs are built against the conductor (`~/.sqx-lab` → `SQX_w1`). A block is only proven by
a build that carries it: that is `/template-run`.

<!-- vendor text follows -->
