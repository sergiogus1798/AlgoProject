## AlgoProject — read this first. Where it differs from the vendor text below, this wins.

The owner's default template has ONE **free** random hole (`#Group#` empty, the whole
vocabulary), so a group is only needed when he asks to restrict what the random condition may
draw from. Ask which blocks and why before authoring one (CLAUDE.md hard rule 11).

**Where the XML goes:** the template's library folder,
`~/Desktop/AlgoData/templates/library/<name>/deps/groups.xml`, not only `engine/out/`.

**Install it on both workers, stopped, never the master** (hard rule 3 checks first). A hybrid
group references custom blocks by key: install those blocks first, in the same installs.

```bash
python3 -m sqx.blocks.install <deps/groups.xml> --role conductor    # same tool as blocks
python3 -m sqx.blocks.install <deps/groups.xml> --role custodian
bin/sqx-lab-install.sh                                              # rebuild the catalogs
```

🤔 Installing groups by file was added 2026-09-25 and has not yet been proven by a build: the
first `/template-run` of a template bound to one must check that its strategies carry the group's
blocks, and write what it saw into `knowhow/authoring/`.

<!-- vendor text follows -->
