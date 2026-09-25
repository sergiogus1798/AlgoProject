#!/bin/bash
# sqx-lab-install — install the vendor's sqx-lab toolkit without /plugin, and refresh it.
#
# WHY THIS EXISTS. sqx-lab ships as a Claude Code plugin, installed with
#   /plugin marketplace add <dir> && /plugin install sqx-lab@sqx-lab
# and those commands DO NOT EXIST in this environment (measured 2026-09-24: the
# VSCode extension answers "/plugin isn't available in this environment"). So the
# toolkit is installed by hand, and this script is that hand — idempotent, so it
# is also how the install is refreshed after downloading a new version.
#
# What a real plugin install gives that this does not: automatic updates. Nothing
# else. The four skills and the two commands behave identically once wired.
#
# THE ONE THING THAT CANNOT BE SYMLINKED: the vendor's commands call
# "${CLAUDE_PLUGIN_ROOT}/doctor.py", a variable only a real plugin install sets.
# They are copied with that variable replaced by the real path, which is why they
# are copies and the skills are links — and why an update needs this script re-run.
#
# Usage:
#   bin/sqx-lab-install.sh [--role ROLE]   wire it up and rebuild the catalogs
#                                         ROLE is the install the catalogs are
#                                         built from; default conductor.
set -euo pipefail

ROLE=conductor
[[ ${1:-} == --role ]] && { ROLE=$2; shift 2; }

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN="$REPO/tools/sqx-lab/plugins/sqx-lab"
SKILLS="$HOME/.claude/skills"
COMMANDS="$HOME/.claude/commands"
INSTALL="$(cd "$REPO" && python3 -c "from core.paths import worker_dir; print(worker_dir('$ROLE'))")"

[[ -d $PLUGIN ]] || { echo "no está el plugin en $PLUGIN"; exit 1; }
[[ -d $INSTALL ]] || { echo "el install $ROLE no existe: $INSTALL"; exit 1; }

echo "sqx-lab $(python3 -c "import json;print(json.load(open('$PLUGIN/.claude-plugin/plugin.json'))['version'])")  ->  $ROLE ($INSTALL)"

mkdir -p "$SKILLS" "$COMMANDS"

# Three of the four the vendor ships. sqx-strategy-project is retired (owner, 2026-09-25):
# it clones any project of the install and deploys into it, against hard rule 10, and
# sqx.projects.builder does that job from the frozen donor. A folder may also exist and be
# deliberately unwired: sqx-spp duplicates this project's own /spp skill. Listing the wired
# ones explicitly is what keeps it that way.
for skill in sqx-custom-block sqx-random-group sqx-strategy-template; do
    ln -sfn "$PLUGIN/skills/$skill" "$SKILLS/$skill"
    echo "  skill   $skill"
done
for skill in sqx-strategy-project sqx-spp; do
    [[ -L $SKILLS/$skill ]] && rm "$SKILLS/$skill" && echo "  retired $skill"
done

# The project's own rules go on top of each vendor SKILL.md, between markers, so a vendor
# update that rewrites the file only needs this script re-run (tools/sqx-lab/LOCAL_PATCHES.md).
python3 - "$PLUGIN/skills" "$REPO/tools/sqx-lab/overlays" <<'PY'
import re, sys
from pathlib import Path
skills, overlays = map(Path, sys.argv[1:])
START, END = "<!-- ALGOPROJECT OVERLAY START -->", "<!-- ALGOPROJECT OVERLAY END -->"
for overlay in sorted(overlays.glob("*.md")):
    skill = skills / overlay.stem / "SKILL.md"
    raw = skill.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"      # the vendor ships CRLF; keep its bytes
    text = re.sub(rf"\n?{START}.*?{END}\n?", "\n", raw.replace("\r\n", "\n"), flags=re.S)
    head, body = re.match(r"(---\n.*?\n---\n)(.*)", text, re.S).groups()
    description = overlay.with_suffix(".description")
    if description.exists():
        head = re.sub(r"^description: .*$", "description: " + description.read_text().strip(),
                      head, count=1, flags=re.M)
    out = f"{head}\n{START}\n{overlay.read_text(encoding='utf-8')}{END}\n" + body.lstrip("\n")
    skill.write_bytes(out.replace("\n", nl).encode("utf-8"))
    print(f"  overlay {overlay.stem}")
PY

# A vendor update erases the local code patches; say so instead of running without them.
for f in skills/sqx-random-group/engine/groups.py skills/sqx-strategy-project/engine/generate.py; do
    grep -q "LOCAL PATCH" "$PLUGIN/$f" || echo "  ⚠️ falta el parche local de $f — tools/sqx-lab/LOCAL_PATCHES.md"
done

for command in sqx-setup sqx-doctor; do
    sed "s|\${CLAUDE_PLUGIN_ROOT}|$PLUGIN|g" "$PLUGIN/commands/$command.md" > "$COMMANDS/$command.md"
    echo "  command /$command"
done

# Catalogs are per install and go stale when its blocks or groups change. Built here
# and not left to the user: a stale catalog does not fail, it invents atoms that are
# not in the install that builds, and the template is then silently wrong.
echo "catálogos:"
python3 "$PLUGIN/skills/sqx-custom-block/engine/bootstrap.py"     --install "$INSTALL" | tail -1
python3 "$PLUGIN/skills/sqx-random-group/engine/bootstrap.py"     --install "$INSTALL" | tail -1
python3 "$PLUGIN/skills/sqx-strategy-template/engine/discover.py" "$INSTALL" | tail -1
python3 "$PLUGIN/skills/sqx-strategy-project/engine/discover.py"  "$INSTALL" | tail -1

echo
python3 "$PLUGIN/doctor.py" | tail -3
