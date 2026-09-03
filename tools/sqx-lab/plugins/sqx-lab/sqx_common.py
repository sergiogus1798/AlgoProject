r"""sqx_common.py — one place for the things all four sqx-lab skills must agree on.

Before this module each skill re-implemented "where is the SQX install / is it valid /
where do I keep state", and they disagreed in ways that hurt users:

  * `sqx-strategy-project` accepted ANY folder, reported "0 projects" as success, and
    then wrote that junk path into the shared install file — silently breaking the
    other three skills.
  * `sqx-strategy-template` raised a bare FileNotFoundError traceback for the same
    mistake.
  * only `sqx-custom-block` / `sqx-random-group` printed something a user could act on.

Everything here exists to make those three behave identically:

  validate_install()      one definition of "is this an SQX install", per-skill needs
  install_error()         one error format, always with the fix
  load/save_shared_install()  ONE stored path, refuses to store an invalid one
  state_dir()             per-machine state OUTSIDE the plugin dir, so a plugin
                          update no longer wipes it (migrates the old location)
  skill_dir()             so --out-dir defaults next to the skill, never into the
                          user's project folder

Import from an engine script (engine/ is 3 levels below the plugin root):

    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
    from sqx_common import validate_install, install_error, ...

Python 3.8+, standard library only.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent

# ── What an SQX install looks like ──────────────────────────────────────────────
# Every path the four skills read, relative to the install ROOT (the top-level folder
# containing internal/ and user/). `config` is the identity marker: if it is missing,
# this is not an SQX install, full stop.
SUBPATHS = {
    "config":          Path("internal/web/SQWIZARD/branding/global/config.xml"),
    "user_indicators": Path("internal/web/SQWIZARD/branding/global/UserCustomIndicators.xml"),
    "custom_blocks":   Path("user/settings/customBlocks.xml"),
    "block_groups":    Path("user/settings/blockGroups.xml"),
    "snippets":        Path("user/extend"),
    "projects":        Path("user/projects"),
    "templates":       Path("user/settings/StrategyTemplates"),
}

# Human wording + the fix, per logical file. Used to build actionable errors instead
# of a traceback or a silent empty catalog.
_MEANING = {
    "config": ("the AlgoWizard indicator vocabulary",
               "Point at the TOP-LEVEL StrategyQuant X folder — the one containing "
               "internal\\ and user\\."),
    "custom_blocks": ("your custom blocks",
                      "This install has no custom blocks yet. Create one in AlgoWizard "
                      "(or use the sqx-custom-block skill) and import it, then re-run."),
    "block_groups": ("your random groups",
                     "This install has no random groups yet. Create one in AlgoWizard "
                     "(or use the sqx-random-group skill) and import it, then re-run."),
    "projects": ("your build projects",
                 "This install has no user/projects folder — open SQX once and create a "
                 "project, then re-run."),
    "templates": ("your strategy templates",
                  "No user/settings/StrategyTemplates folder — build a template with the "
                  "sqx-strategy-template skill first."),
}


def validate_install(root, need=("config",)) -> dict:
    """Resolve an install root and report exactly what is and isn't there.

    `need` names the logical files this caller cannot work without. The result always
    carries `is_sqx` (config.xml present) separately from `ok` (everything in `need`
    present), so a caller can tell "not an SQX folder at all" from "an SQX folder that
    has no groups yet" — two problems with two different fixes.
    """
    info: dict = {"root": str(root), "resolved": {}, "missing": [],
                  "exists": False, "is_sqx": False, "ok": False}
    if not root or not str(root).strip():
        info["reason"] = "no install folder given"
        return info
    p = Path(str(root).rstrip("\\/"))
    info["root"] = str(p)
    if not p.is_dir():
        info["reason"] = "folder does not exist"
        return info
    info["exists"] = True
    for name, sub in SUBPATHS.items():
        target = p / sub
        info["resolved"][name] = str(target) if target.exists() else None
    info["is_sqx"] = info["resolved"]["config"] is not None
    info["missing"] = [n for n in need if not info["resolved"].get(n)]
    info["ok"] = info["is_sqx"] and not info["missing"]
    if not info["is_sqx"]:
        info["reason"] = "not a StrategyQuant X install folder"
    elif info["missing"]:
        info["reason"] = "install is missing files this skill needs"
    return info


def install_error(info: dict, rerun: str | None = None) -> str:
    """One error format for every skill. Says what's wrong, shows the path it looked
    for, and gives the concrete next command. Never a traceback."""
    lines = [f"FAIL: {info.get('reason', 'unusable install')}: {info['root']}"]
    root = Path(info["root"])
    if not info["exists"]:
        lines.append("  That folder does not exist on this machine.")
        lines.append("  " + _MEANING["config"][1])
    elif not info["is_sqx"]:
        lines.append(f"  expected: {root / SUBPATHS['config']}   (missing)")
        lines.append("  " + _MEANING["config"][1])
    else:
        for name in info["missing"]:
            what, fix = _MEANING.get(name, (name, ""))
            lines.append(f"  missing {what}: {root / SUBPATHS[name]}")
            if fix:
                lines.append(f"  {fix}")
    if rerun:
        lines.append(f'  Then re-run: {rerun}')
    return "\n".join(lines)


# ── Per-machine state, OUTSIDE the plugin install dir ───────────────────────────
# Catalogs and the stored install path used to live inside the plugin's own cache
# folder, which is version-scoped (…/cache/sqx-lab/sqx-lab/1.1.0/) — so every plugin
# update silently threw away the user's setup. State now lives in ~/.sqx-lab and
# survives updates; SQX_LAB_HOME overrides it (CI, sandboxes, read-only homes).
LEGACY_INSTALL_FILE = PLUGIN_ROOT / "sqx-install.txt"


def state_dir() -> Path:
    env = os.environ.get("SQX_LAB_HOME")
    base = Path(env) if env else Path.home() / ".sqx-lab"
    try:
        base.mkdir(parents=True, exist_ok=True)
    except OSError:
        return PLUGIN_ROOT          # last-resort fallback: old behaviour
    return base


def install_file() -> Path:
    return state_dir() / "sqx-install.txt"


def load_shared_install() -> str | None:
    """The stored SQX folder, or None. Migrates the pre-1.2 plugin-root file on first
    read so an existing user never has to answer the setup question again — but ONLY
    after the legacy value passes validate_install(). The legacy file is the very one
    the old project-skill bug could write a junk path into; copying it unvalidated
    would freeze that poisoning into the update-surviving state dir. An invalid legacy
    value is treated as "not set" (returns None) and the legacy file is left alone."""
    new = install_file()
    try:
        val = new.read_text(encoding="utf-8").strip()
        if val:
            return val
    except OSError:
        pass
    try:
        val = LEGACY_INSTALL_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not val:
        return None
    if not validate_install(val)["is_sqx"]:
        return None                       # junk from the pre-1.2 bug — do not persist it
    if new != LEGACY_INSTALL_FILE:
        try:
            new.write_text(val + "\n", encoding="utf-8")
        except OSError:
            pass
    return val


def save_shared_install(root) -> bool:
    """Store the install path for all four skills — but ONLY if it really is an SQX
    install. This is the guard for the bug where pointing one skill at a wrong folder
    poisoned the shared path and silently broke the other three."""
    info = validate_install(root)
    if not info["is_sqx"]:
        return False
    try:
        install_file().write_text(str(info["root"]).strip() + "\n", encoding="utf-8")
        return True
    except OSError:
        return False


# ── Where a skill's own files live ──────────────────────────────────────────────
def skill_dir(engine_file) -> Path:
    """Skill root for an engine/ script — the anchor for catalogs and outputs.

    --out-dir used to default to "." (the cwd), so bootstrapping from the user's
    project directory — which is where Claude Code actually starts — dropped a ~500 KB
    catalog.json into their repo. Defaulting to the skill dir makes the catalog land in
    the same place no matter where the command is run from.
    """
    return Path(engine_file).resolve().parent.parent


def find_catalog(engine_file, name: str = "catalog.json") -> Path | None:
    """Locate an existing catalog, tolerating both historical layouts (skill root for
    blocks/groups, engine/ for template/project) and a cwd-relative path."""
    sd = skill_dir(engine_file)
    for cand in (Path(name), sd / name, sd / "engine" / name):
        if cand.exists():
            return cand.resolve()
    return None


# ── Console helpers ─────────────────────────────────────────────────────────────
def utf8_stdout() -> None:
    """Windows consoles default to a non-UTF-8 codepage; the catalogs use ⭐/✦/◆."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass


def require_python(minimum=(3, 8)) -> None:
    if sys.version_info < minimum:
        need = ".".join(str(x) for x in minimum)
        have = ".".join(str(x) for x in sys.version_info[:3])
        raise SystemExit(
            f"FAIL: sqx-lab needs Python {need}+ — this interpreter is {have}\n"
            f"  interpreter: {sys.executable}\n"
            f"  On Windows try the launcher instead:  py -3 engine/<script>.py ...")
