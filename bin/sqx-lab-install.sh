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

# The four the vendor ships. A fifth folder may exist and be deliberately unwired:
# sqx-spp duplicates this project's own /spp skill, and two overlapping SPP skills
# is worse than one. Listing the four explicitly is what keeps it that way.
for skill in sqx-custom-block sqx-random-group sqx-strategy-template sqx-strategy-project; do
    ln -sfn "$PLUGIN/skills/$skill" "$SKILLS/$skill"
    echo "  skill   $skill"
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
