# Creating and modifying SQX projects programmatically

**Yes, this works.** Verified end-to-end on the worker on 2026-09-02: a project was created from a
`.cfx`, modified, reloaded, verified, and removed.

The earlier claim in this repo that "there is no config-write path" was too narrow. It is true only
of a project **currently loaded by a running GUI**. Everything below is the supported path.

## The two mechanisms

| | What it does | Needs |
|---|---|---|
| **`sqx-strategy-project` skill** | Authors a `project.cfx` by cloning a donor project and wiring N templates as N build tasks | Installed at `~/.claude/skills/sqx-strategy-project`. Deploys with **SQX closed** |
| **`-project` CLI/HTTP API** | Imports/exports a project config into a running instance | Worker `:5060` any time; master `:5050` **only with the GUI closed** |

## The `-project` verb (from `sqcli -help`)

```
action: [list, start, startOnlyTask, startFromTask, stop, pause, resume,
         remove, status, loadconfig, saveconfig]
name:   (optional) Project name
file:   (optional) Path of the config file
task:   (optional) Task number, indexed from 1
```

## Verified create + modify cycle

```bash
W=http://localhost:5060/call

# 1. A "project template" .cfx is the MULTI-FILE form: config.xml + <Type>-Task<N>.xml.
#    Copy an existing project as the donor.
cp ~/Desktop/SQX/user/projects/XAUUSD/project.cfx /tmp/tmpl.cfx

# 2. Create a project from it. Creates ~/Desktop/SQX_w1/user/projects/<name>/
curl -g "$W?cmd=-project%20action=loadconfig%20name=MyProject%20file=/tmp/tmpl.cfx"
#   -> Project loaded 'MyProject'.

# 3. Modify: unzip, edit the XML, rezip.
mkdir /tmp/mod && cd /tmp/mod && unzip -q /tmp/tmpl.cfx
sed -i 's|<RetestWithHigherPrecision use="false"|<RetestWithHigherPrecision use="true"|' \
    AutomaticRetest-Task3.xml
zip -rq /tmp/modified.cfx . -x '.*'

# 4. Load it back.
curl -g "$W?cmd=-project%20action=loadconfig%20name=MyProject%20file=/tmp/modified.cfx"

# 5. Remove when done.
curl -g "$W?cmd=-project%20action=remove%20name=MyProject"
```

Verify what SQX actually stored by reading the project back — never trust the load message alone:

```bash
python3 tools/sqx-inspect/dump_project.py \
    ~/Desktop/SQX_w1/user/projects/MyProject/project.cfx | head -40
```

## Four traps, each hit during verification

1. **`loadconfig` never overwrites.** Loading into an existing name creates `MyProject(2)` and
   leaves the original untouched. The load message says `Project loaded 'MyProject(2)'` — read it.
   To genuinely replace a project: `action=remove name=X` first, then `loadconfig`.

2. **`saveconfig` output is NOT loadable.** `saveconfig` writes a `.cfx` containing only
   `config.xml`; `loadconfig` rejects it with `Cannot load config. Selected config is not a project
   template`. The verbs are asymmetric. To get a loadable template, copy an existing
   `project.cfx` from `user/projects/<name>/` — that is the multi-file form. `~/Desktop/Benchmark.cfx`
   is also single-file and equally unloadable.

3. **URL-encode only space→`%20`, `?`, `&`, `#`.** The server reads the query literally. A project
   name with parentheses must keep them literal — `name=MyProject(2)` works,
   `name=MyProject%282%29` fails with `Project 'MyProject%282%29' does not exist.`

4. **A loaded project still cannot be edited on disk.** SQX rewrites every `project.cfx` on save and
   exit. The API path works because SQX performs the write itself. Never `sed` a `project.cfx` that
   a running instance holds.

## Which install to target

- **Worker `:5060`** — always safe, runs headless, no GUI to conflict with. This is where agents
  should author and test project configs. It only has its 5 default projects, so copy in a donor
  `project.cfx` first.
- **Master `:5050`** — the command API is unavailable while the GUI runs. It answers
  `Error: CLI not ready.` Using it means closing the GUI, which is the SQX-lifecycle lane.

The practical workflow: **author and verify on the worker, then move the finished `.cfx` to the
master during a deliberate maintenance window.**
