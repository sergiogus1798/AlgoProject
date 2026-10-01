## AlgoProject — read this first. Where it differs from the vendor text below, this wins.

Owner, 2026-09-25: this is the project's template skill; the old `/strategy-template` is retired.
Nothing here starts SQX or burns CPU. Building the template on a market is `/template-run`.

**1 · Ask the logic, always** (CLAUDE.md hard rule 11). "Closes above the band" fires on every
bar of a move, "crosses above it" fires once: different strategies. List the readings you see —
which band, state or transition, which price, which shift — and ask. The vendor's "clarify only
what you cannot infer" does not apply to the entry logic.

**2 · The owner's defaults win** (`sqx/templates/README.md`). Apply them silently, then say which
ones you applied:

| unspecified | assume |
|---|---|
| direction | long |
| extra conditions | ONE random condition, **free**: `#Group#` empty, the whole vocabulary |
| what he named | **fixed** exactly as said, never parametrised |
| periods, deviations — any number he did not name | **random**: the builder draws a value per strategy |
| `Shift` | 1 |

The vendor's thesis-driven shapes — filter + trigger bound to clean groups, stop/limit entries,
session gating, multi-timeframe, short or mirrored sides — are used **only when the idea or the
owner asks for one**. Do not launch the research agent for a default template.

**3 · Default path** — from the repo root, not the skill folder:

```bash
python3 -m sqx.inspect.vocabulary <term>         # does the exact block exist? native or his own
# missing -> author it with sqx-custom-block (its own overlay says how to install it)
python3 -m sqx.templates.build <name> <library>/<name>/deps/blocks.xml <CBlock_key> \
    <library>/<name>/template.sqx                 # market_long: his condition AND a free hole
# the condition goes in a one-item group, <name>Signal, whose numeric params the builder draws at
# random (owner, 2026-09-25) — also written to <library>/<name>/deps/groups.xml: install it (step 6).
# A frozen block would carry ONE period in every strategy; SQX refuses random params on it.
# a NATIVE block: pass the conductor's AlgoWizard config.xml instead of deps/blocks.xml —
#   ~/Desktop/SQX_w1/internal/web/SQWIZARD/branding/global/config.xml
# fix what the owner named with --param, e.g. an EMA: --param '#Type#=1'
```

Never substitute the nearest existing block for the one the owner described. `vocabulary` printing
`NO GROUP POOLS IT — unusable in a template` concerns the random hole only: the fixed half of the
signal reaches any block directly, pooled or not.

**4 · Another shape** — the vendor flow below (catalog, design, `from_design`, validate), run from
the skill folder. Its output in `engine/out/` is scratch: copy it into the library (step 5).

**5 · Every template lands in the library**, `~/Desktop/AlgoData/templates/library/<name>/`:
`template.sqx`, `brief.md` (Spanish, the thesis and every default applied), `brief.json`,
`manifest.json`, `deps/` (`blocks.xml`, `groups.xml` when it has any). Copy the structure of
`keltnerUpperCrossUp`. The name never carries a symbol or a timeframe — those are rows in `runs.csv`.

```bash
python3 -m sqx.templates.registry --set name=<name> --set archetype=<breakout|meanReversion|…> \
    --set shape=<market_long|…> --set entry=… --set created=<date> --set origin=authored \
    --set status=validated
```

**6 · Its blocks and groups go into both workers**, stopped, never the master (CLAUDE.md hard
rule 3: check `ListAgents`, `ls -lt <worker>/user/projects | head` and the log first):

```bash
python3 -m sqx.blocks.install <deps/blocks.xml> --role conductor    # then --role custodian
python3 -m sqx.blocks.install <deps/groups.xml> --role conductor    # same tool for groups
python3 -m sqx.inspect.vocabulary --diff custodian                   # must report no gap
bin/sqx-lab-install.sh                                               # the catalogs are stale now
```

A template referencing a block the building install lacks does not error: it disappears from the
build. The vendor's "import into AlgoWizard and run a Build" does not apply here — the owner rarely
opens the GUI. `status=buildConfirmed` is written only by `/template-run`.

<!-- vendor text follows -->

## One direction only (hard rule 13, owner 2026-10-01)

A template trades long OR short, never both: no template with a `Long entry` and a `Short entry`
that both open trades, and no symmetric both-direction template. A short idea is its own template.
`sqx.projects.builder` refuses a two-sided template.

