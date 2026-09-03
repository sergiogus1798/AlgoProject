---
description: One-time setup — point sqx-lab at your StrategyQuant X install and bootstrap all four skills.
argument-hint: "[path to your StrategyQuant X folder]"
allowed-tools: Bash, Read, AskUserQuestion
---

# sqx-lab setup

Get all four skills (`sqx-custom-block`, `sqx-random-group`, `sqx-strategy-template`,
`sqx-strategy-project`) working in one pass, so the user never has to answer the
install question four times.

User-supplied install folder (may be empty): `$1`

## 1 — Establish the install folder

```bash
python "${CLAUDE_PLUGIN_ROOT}/doctor.py"
```

- **`$1` was given** → use it.
- **Doctor already reports a valid SQX install** → say which folder, and only re-ask if
  the user says it's wrong.
- **Otherwise ASK.** Run `python "${CLAUDE_PLUGIN_ROOT}/skills/sqx-custom-block/engine/discover.py"`
  to *suggest* installs found on this machine, show the candidates, and have the user
  **confirm or correct** one. A discovered path is a suggestion, never a silent default.

The folder wanted is the **top-level** StrategyQuant X folder — the one containing
`internal\` and `user\` (e.g. `C:\StrategyQuantX144`), not a subfolder.

## 2 — Bootstrap all four

Run these four in order. `<INSTALL>` is the confirmed folder; after the first one
succeeds the path is stored in `~/.sqx-lab/sqx-install.txt` and the rest pick it up, so
you may drop the argument from #2–#4.

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/sqx-custom-block/engine/bootstrap.py"     --install "<INSTALL>"
python "${CLAUDE_PLUGIN_ROOT}/skills/sqx-random-group/engine/bootstrap.py"     --install "<INSTALL>"
python "${CLAUDE_PLUGIN_ROOT}/skills/sqx-strategy-template/engine/discover.py" "<INSTALL>"
python "${CLAUDE_PLUGIN_ROOT}/skills/sqx-strategy-project/engine/discover.py"  "<INSTALL>"
```

Each writes its catalog next to its own skill. If one fails, its error names the exact
missing file and the fix — read it out and stop; don't run the rest against a bad path.

Steps 3 and 4 are expected to warn on a fresh install with no custom blocks or groups
yet. That is not a failure — it just means the chain starts at `sqx-custom-block`.

## 3 — Report

```bash
python "${CLAUDE_PLUGIN_ROOT}/doctor.py"
```

Summarise for the user:

- the install now in use,
- what was found (atoms · custom indicators · blocks · groups · projects · templates),
- **any broken groups**, and that `/sqx-doctor` explains how to repair them,
- the one thing to do next — usually: author blocks (`sqx-custom-block`) if they have
  none, pool them (`sqx-random-group`) if they have blocks but no groups, or design a
  template (`sqx-strategy-template`) if the chain is already intact.

Keep it to a short table plus one recommended next step.
