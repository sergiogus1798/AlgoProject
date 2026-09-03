r"""doctor.py — one health check for the whole sqx-lab toolkit.

Answers, in one run, the questions a stuck user actually has:
  * is my Python OK?
  * which SQX install is the toolkit pointed at, and is it still there?
  * has each skill been bootstrapped, and against WHICH install?
  * is the block -> group -> template -> project chain actually intact?
  * what is the single next thing I should do?

Run:  python doctor.py            (from the plugin root)
Exit: 0 = healthy, 1 = something needs attention.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sqx_common import (  # noqa: E402
    PLUGIN_ROOT, SUBPATHS, install_file, load_shared_install, state_dir,
    utf8_stdout, validate_install)

SKILLS = ["sqx-custom-block", "sqx-random-group", "sqx-strategy-template",
          "sqx-strategy-project"]

OK, WARN, BAD = "  OK  ", " WARN ", " FAIL "

# fix-list severity ranks — lower prints first ("most important first" is a promise
# the header makes; the list is sorted by (rank, insertion order) before printing)
RANK_PYTHON = 0      # no usable interpreter — nothing else can run
RANK_INSTALL = 10    # no/invalid SQX install — every skill is blocked
RANK_CHAIN = 20      # the block->group->template->project chain is missing a link
RANK_STALE = 30      # a catalog exists but is wrong/old — re-bootstrap it
RANK_BOOTSTRAP = 40  # a skill was simply never bootstrapped
RANK_ADVISORY = 50   # worth doing, blocks nothing

_fixes: list[tuple[int, int, str]] = []   # (rank, insertion order, fix text)


def line(status: str, label: str, detail: str = "") -> None:
    print(f"[{status}] {label}" + (f"  —  {detail}" if detail else ""))


def problem(fix: str, rank: int = RANK_ADVISORY) -> None:
    """Register a numbered fix. `rank` decides where it prints in the final list
    (lower = more important); insertion order breaks ties."""
    _fixes.append((rank, len(_fixes), fix))


def _age(p: Path) -> str:
    try:
        days = (time.time() - p.stat().st_mtime) / 86400
    except OSError:
        return "?"
    return "today" if days < 1 else f"{int(days)}d ago"


def check_python() -> None:
    v = ".".join(str(x) for x in sys.version_info[:3])
    if sys.version_info < (3, 8):
        line(BAD, f"Python {v}", "sqx-lab needs 3.8+")
        problem("Install Python 3.8+ and re-run (on Windows: `py -3 --version`).",
                RANK_PYTHON)
    else:
        line(OK, f"Python {v}", sys.executable)


def check_install() -> dict | None:
    stored = load_shared_install()
    print(f"\nSTATE  {state_dir()}")
    if not stored:
        line(BAD, "SQX install", f"not set yet ({install_file()})")
        problem("Run /sqx-setup, or tell any sqx-lab skill your StrategyQuant X folder "
                "(the top-level one, containing internal\\ and user\\).", RANK_INSTALL)
        return None
    info = validate_install(stored)
    if not info["exists"]:
        line(BAD, "SQX install", f"{stored} — folder is gone")
        problem(f"The stored install no longer exists. Re-run /sqx-setup with the "
                f"current folder (edit or delete {install_file()}).", RANK_INSTALL)
        return info
    if not info["is_sqx"]:
        line(BAD, "SQX install", f"{stored} — no config.xml, not an SQX install")
        problem("Point the toolkit at the TOP-LEVEL StrategyQuant X folder via /sqx-setup.",
                RANK_INSTALL)
        return info
    line(OK, "SQX install", stored)
    for name in ("custom_blocks", "block_groups", "projects", "templates"):
        present = info["resolved"].get(name)
        label = f"  {name.replace('_', ' ')}"
        if present:
            line(OK, label, str(SUBPATHS[name]))
        else:
            line(WARN, label, f"missing ({SUBPATHS[name]}) — some skills will be limited")
    return info


def _install_sources_mtime(install_root: str) -> float | None:
    """The newest mtime of the install files the catalogs are built FROM
    (customBlocks.xml / blockGroups.xml). None if neither is statable."""
    newest = None
    for key in ("custom_blocks", "block_groups"):
        try:
            mt = (Path(install_root) / SUBPATHS[key]).stat().st_mtime
        except OSError:
            continue
        newest = mt if newest is None else max(newest, mt)
    return newest


def check_catalogs(info: dict | None) -> None:
    print("\nCATALOGS")
    want = str(info["root"]) if info and info.get("is_sqx") else None
    for s in SKILLS:
        sd = PLUGIN_ROOT / "skills" / s
        found = None
        for cand in (sd / "catalog.json", sd / "engine" / "catalog.json"):
            if cand.exists():
                found = cand
                break
        if not found:
            line(WARN, s, "not bootstrapped yet")
            problem(f"Bootstrap {s} (or just run /sqx-setup once).", RANK_BOOTSTRAP)
            continue
        built_for = None
        try:
            data = json.loads(found.read_text(encoding="utf-8", errors="replace"))
            built_for = data.get("install") or (data.get("meta") or {}).get("install")
        except (OSError, ValueError):
            line(BAD, s, f"catalog unreadable: {found}")
            problem(f"Delete {found} and re-bootstrap {s}.", RANK_STALE)
            continue
        detail = _age(found)
        if want and built_for and os.path.normcase(str(built_for).rstrip("\\/")) != \
                os.path.normcase(want.rstrip("\\/")):
            line(WARN, s, f"built {detail} from a DIFFERENT install: {built_for}")
            problem(f"Re-bootstrap {s} against {want} (stale catalog = phantom atoms).",
                    RANK_STALE)
            continue
        # staleness: a catalog that records its install can be checked against that
        # install's block/group files — if they changed after the catalog was built,
        # the catalog describes a vocabulary that no longer exists
        if built_for:
            src_mtime = _install_sources_mtime(str(built_for))
            try:
                cat_mtime = found.stat().st_mtime
            except OSError:
                cat_mtime = None
            if src_mtime and cat_mtime and cat_mtime < src_mtime:
                line(WARN, s, f"STALE catalog (built {detail}) — the install changed "
                              f"after this catalog was built")
                problem(f"Re-bootstrap {s}: stale catalog — the install's customBlocks/"
                        f"blockGroups changed after this catalog was built (phantom or "
                        f"missing atoms until then).", RANK_STALE)
                continue
        line(OK, s, f"catalog built {detail}")


def check_chain() -> None:
    """The part that actually decides whether the user can build anything."""
    print("\nCHAIN  (block -> group -> template -> project)")
    tpl = PLUGIN_ROOT / "skills" / "sqx-strategy-template" / "engine" / "catalog.json"
    if not tpl.exists():
        line(WARN, "groups", "template catalog missing — run /sqx-setup")
        return
    try:
        d = json.loads(tpl.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        line(BAD, "groups", "template catalog unreadable")
        return
    cond = d.get("clean_condition_groups", [])
    val = d.get("clean_value_groups", [])
    broken = d.get("broken_groups", [])
    repairs = d.get("repair_manifest", [])
    n_blocks = d.get("n_custom_blocks", 0)
    line(OK if n_blocks else WARN, "custom blocks",
         f"{n_blocks} in customBlocks.xml")
    if not n_blocks:
        problem("No custom blocks in customBlocks.xml — the chain starts there: author "
                "one with the sqx-custom-block skill and import it in AlgoWizard, then "
                "re-bootstrap.", RANK_CHAIN)
    line(OK if len(cond) >= 2 else WARN, "clean Condition groups",
         f"{len(cond)} (need >=2: a filter AND a trigger)")
    if len(cond) < 2:
        problem(f"Only {len(cond)} clean Condition group(s) — templates need a filter "
                f"AND a trigger pool. Build one with the sqx-random-group skill (or "
                f"repair a broken group), then re-bootstrap.", RANK_CHAIN)
    line(OK if val else BAD, "clean Value groups",
         f"{len(val)} (need >=1 for stop / stop_long / mtf_filter — "
         f"the build-confirmed shapes)")
    if broken:
        n = sum(len(r.get("rebuild", [])) for r in repairs)
        line(WARN, "broken groups",
             f"{len(broken)} excluded, {n} missing blocks: "
             + ", ".join(g["name"] for g in broken[:4]))
        problem(f"Repair them: the sqx-custom-block skill can re-author all {n} missing "
                f"blocks from `repair_manifest` in {tpl.name} — ask it to "
                f'"repair my broken groups".', RANK_ADVISORY)
    if not val:
        broken_val = [g["name"] for g in broken if g.get("type") == "Value"]
        if broken_val:
            problem(f"Repairing {', '.join(broken_val)} unlocks every build-confirmed "
                    f"strategy shape — do this first.", RANK_CHAIN)
        else:
            problem("Build a Value (price-level) group with the sqx-random-group skill "
                    "to unlock the stop / mtf_filter shapes.", RANK_CHAIN)

    prj = PLUGIN_ROOT / "skills" / "sqx-strategy-project" / "engine" / "catalog.json"
    if prj.exists():
        try:
            p = json.loads(prj.read_text(encoding="utf-8", errors="replace"))
            nproj = len([x for x in p.get("projects", []) if x.get("build_tasks")])
            ntpl = sum(len(v) for v in p.get("template_sets", {}).values())
            line(OK if nproj else WARN, "clonable base projects", str(nproj))
            line(OK if ntpl else WARN, "strategy templates on disk", str(ntpl))
            if not nproj:
                problem("Create one build project in SQX (any template task) — the "
                        "project skill clones, it cannot define a data feed.", RANK_CHAIN)
        except (OSError, ValueError):
            pass


def main() -> int:
    utf8_stdout()
    print("=" * 68)
    print("sqx-lab doctor")
    print("=" * 68)
    check_python()
    info = check_install()
    check_catalogs(info)
    check_chain()
    print("\n" + "=" * 68)
    if not _fixes:
        print("All green — the full block -> group -> template -> project chain is usable.")
        return 0
    print(f"{len(_fixes)} thing(s) to fix, most important first:\n")
    for i, (_rank, _seq, f) in enumerate(sorted(_fixes), 1):
        print(f"  {i}. {f}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
