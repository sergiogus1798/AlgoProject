# What a StrategyQuant project (`project.cfx`) IS

The abstract model behind `sqx-strategy-project`. Read once; the engine encodes all of it.

## The container

A `project.cfx` (in `<INSTALL>\user\projects\<NAME>\`) is a **ZIP archive**, not a single XML:

```
project.cfx (ZIP)
├── config.xml              # the project manifest: <Project><Tasks/><Databanks/></Project>
├── Build-Task1.xml         # build task #1 — EMBEDS ~3 MB of that task's full build config
├── Build-Task2.xml         # build task #2 …
│   …                       # one per active build task
├── GoToTask-Task1.xml      # an inactive helper task (verbatim, never edited)
└── StopAndStart-Task1.xml  # an inactive helper task (verbatim, never edited)
```

A 24-task project is **27 ZIP entries**: 1 config + 24 task XMLs + 2 helpers.

## `config.xml` — the manifest

```xml
<Project name="FX_ID_60_MKT" version="141.2225">
  <Tasks>
    <Task type="Build" name="…" taskXMLFile="Build-Task1.xml"
          templateFile="…\BuildSettings.cfx" title="BS-…_LS" />
    …
    <Task name="Go To Task"   type="GoToTask"     taskXMLFile="GoToTask-Task1.xml"    active="false" />
    <Task name="Stop &amp; Start" type="StopAndStart" taskXMLFile="StopAndStart-Task1.xml" active="false" />
  </Tasks>
  <Databanks>
    <Databank name="Results"            … position="0" />   <!-- the 5 SYSTEM databanks -->
    <Databank name="Last generation"    … position="1" />
    <Databank name="Initial population" … position="2" />
    <Databank name="Strategies to improve" … position="3" />
    <Databank name="Existing portfolio" … position="4" />
    <Databank name="BS-…_LS" … position="1000" />          <!-- one per build task -->
    …
  </Databanks>
</Project>
```

Notes that matter:
- The **`<Project version=>`** can read `141.x` even on a 144 install — it is NOT bumped. **Preserve it
  verbatim** (the engine parses and keeps it; never hardcode a version literal).
- On a `<Task>`, **`templateFile`** is the **task-SETTINGS preset** (`.cfx`) — the optimizer/build
  configuration, the SAME for every task. It is **NOT** the strategy template. Carried over unchanged.
- On a `<Task>`, **`title`** is the task's **result databank label** — a *display* mirror of the real
  output binding, which lives inside the task XML (see below). Keep them consistent.
- The **2 inactive helper tasks** and the **5 system databanks** are structural — preserve them or the
  project won't load. The engine re-emits them from the base, not from a hardcoded list of names beyond
  the system set it sanity-checks.

## `Build-Task{N}.xml` — the embedded build (where the holes are)

Each is ~3 MB and embeds the entire build configuration. This skill treats it as **opaque except four
surgical points**, swapped at the byte level (never reserialized):

| # | Anchor (regex) | What it sets | Skill role |
|---|---|---|---|
| a | `<StrategyType … templateFile="…">` | the strategy template `.sqx` to build | **the strategy** (required) |
| b | `<Databank label="Output databank" name="Output" value="…">` | where built strategies SAVE | **output databank** (required, unique) |
| c | `class="AvgTradesPerMonth" … <Numeric-Value value="N">` | a min-activity acceptance gate | optional override |
| d | `<StopCondition … minutes="N">` | per-task compute time cap | optional override |

**The output-databank trap:** built strategies save to the value of (b) *inside the task XML*, NOT to
`config.xml`'s `<Task title=>`. Clone a task without rewriting (b) and all clones write to the donor's
databank — they overwrite each other. (b) is the difference between "24 tasks, 24 result sets" and "24
tasks, 1 result set." The engine swaps it per task and verifies `internal Output == task title`.

Other settings that live *only* inside the task XML and are therefore **inherited from the donor**, not
exposed as holes: the data feed / symbol / timeframe (`<Datas>`), the full exit stack, all other
acceptance conditions, `databank="Existing portfolio"` (seed), `improveDatabank="Results"`. To change
any of these, clone a **different base project** whose donor task already has them.

## The cloning mechanic (what `generate.py` does)

```
read base.cfx (ZIP)
  donor          = base's build task #i           (its 3 MB = the inherited settings)
  settings_preset = that task's config <Task templateFile>
for each chosen template T:
  clone donor bytes; swap (a) → T's path, (b) → T's own databank, (c)/(d) if overridden
regenerate config.xml:
  <Project>           : base's attribs, name swapped
  inactive <Task>s    : preserved verbatim
  <Databank>s         : keep every non-(old-build-output); append one per new task
write new project.cfx + empty databanks/<name>/ folders
verify: member count · build-task count · unique+registered output DBs · system DBs survive ·
        each templateFile resolves on disk · internal Output == title
```

## The validity gap (why clone, not synthesize)

A structurally valid `config.xml` + parseable task XMLs is **necessary but not sufficient** — only
SQX opening the project and running a Build proves it. The 3 MB of embedded settings, the data binding,
and the acceptance protocol are far past what's worth regenerating by hand. So the skill **transplants
the proven holes into a donor that already builds** and changes nothing else. The oracle is an
AlgoWizard Build, not the schema.

## Deployment rules

- **`templateFile` is ABSOLUTE** — build-144 has no relative/variable form. Resolve template paths
  against the **target install**; keep the `.sqx` inside `user/settings/StrategyTemplates/…` so a
  folder copy travels. Cross-machine needs the install at the same root, or a one-line prefix repath.
- **SQX MUST be closed** when writing into `user/projects/…` — SQX rewrites `project.cfx` on close and
  clobbers external edits.
- Old databank **folders on disk** are harmless to leave; dropping a databank from `config.xml` only
  unregisters it.

## Lineage (lab → product)

This engine distills two BUILD-CONFIRMED one-off scripts:
- `…\FX_ID_60_MKT_NEW\_attach_breakout_fleet.py` — replaced a project's tasks with 24 breakout tasks,
  each its own output databank + `AvgTradesPerMonth>2` + `5-min` cap. **Build-confirmed 2026-06-10.**
- `_build_long_project.py` — install-parametric clone-to-new-project
  with per-target template repathing. **Build-confirmed 2026-06-10.**

The distillation drops their hardcoded install paths and stale `version` literal: it is
**install-parametric** (install + base + templates are inputs) and **base-derived** (the project tag,
system databanks, and inactive tasks come from the base, not from code). Every clone it emits is
byte-identical to `donor + exactly the 4 swaps`.
