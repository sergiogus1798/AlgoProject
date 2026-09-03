r"""
discover.py — read a StrategyQuant X build-144 install into catalog.json: the base
projects you can CLONE, the strategy-template sets you can wire as tasks, and the
task-settings presets in play.

    python engine/discover.py "C:\StrategyQuantX"

catalog.json is written next to the engine and is the source of truth for what THIS
install can clone + wire. Never invent a project or template name — consult it.
"""
import os
import re
import sys
import json
import zipfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))

# Shared per-machine state + install validation live in sqx_common at the plugin root.
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
from sqx_common import (  # noqa: E402
    load_shared_install, save_shared_install, validate_install, install_error, skill_dir)

CATALOG = os.path.join(HERE, "catalog.json")


# cheap pulls from the (3 MB) first build task — symbol/timeframe for display only
_SYMBOL_RE = re.compile(r'<(?:Symbol|symbol)\b[^>]*\bvalue="([^"]+)"')
_TF_RE = re.compile(r'<(?:Timeframe|timeframe|ChartTF|chartTF)\b[^>]*\bvalue="([^"]+)"')
_DATA_RE = re.compile(r'\b(?:symbol|chartSymbol)="([^"]+)"')
_TFA_RE = re.compile(r'\b(?:timeframe|chartTimeframe|chartTF)="([^"]+)"')


def _sample_market(task_bytes):
    """Best-effort (symbol, timeframe) from a build task — display sugar, not load-bearing."""
    head = task_bytes[:200_000].decode("utf-8", "replace")
    sym = (_SYMBOL_RE.search(head) or _DATA_RE.search(head))
    tf = (_TF_RE.search(head) or _TFA_RE.search(head))
    return (sym.group(1) if sym else None, tf.group(1) if tf else None)


def scan_projects(install):
    """Every user/projects/*/project.cfx -> {name, version, build_tasks, databanks,
    template_tasks, settings_preset, symbol, timeframe, path}."""
    root = os.path.join(install, "user", "projects")
    out = []
    if not os.path.isdir(root):
        return out
    for entry in sorted(os.listdir(root)):
        cfx = os.path.join(root, entry, "project.cfx")
        if not os.path.isfile(cfx):
            continue
        try:
            with zipfile.ZipFile(cfx) as z:
                cfg = ET.fromstring(z.read("config.xml").decode("utf-8"))
                tasks = cfg.find("Tasks").findall("Task")
                build = [t for t in tasks if t.get("type") == "Build"]
                tmpl = [t for t in build if t.get("templateFile")]
                preset = build[0].get("templateFile") if build else None
                sym, tf = (None, None)
                if build:
                    first = build[0].get("taskXMLFile")
                    if first in z.namelist():
                        sym, tf = _sample_market(z.read(first))
            out.append({
                "name": cfg.get("name"), "folder": entry, "version": cfg.get("version"),
                "build_tasks": len(build),
                "databanks": len(cfg.find("Databanks").findall("Databank")),
                "settings_preset": preset,
                "symbol": sym, "timeframe": tf,
                "path": cfx,
            })
        except Exception as e:  # a non-project .cfx or a half-written file — skip, note
            out.append({"folder": entry, "path": cfx, "error": str(e)})
    return out


def scan_templates(install):
    """user/settings/StrategyTemplates/** -> {subdir or '<root>': [abs .sqx paths]}."""
    root = os.path.join(install, "user", "settings", "StrategyTemplates")
    out = {}
    if not os.path.isdir(root):
        return out
    for dirpath, _dirs, files in os.walk(root):
        sqx = sorted(os.path.join(dirpath, f) for f in files if f.lower().endswith(".sqx"))
        if sqx:
            key = os.path.relpath(dirpath, root).replace("\\", "/")
            out[key if key != "." else "<root>"] = sqx
    return out


def discover(install):
    """Read an install into catalog.json.

    Validates FIRST. This used to accept any folder, print "0 projects / 0 templates"
    as if that were success, and then store the bad path for all four skills — the
    single worst failure mode in the toolkit. Now a non-install is a hard, explained
    stop, and an SQX install with no projects yet says so in those words.
    """
    info = validate_install(install, need=("projects",))
    if not info["ok"]:
        raise SystemExit(install_error(
            info, rerun='python engine/discover.py "<your SQX install folder>"'))
    install = info["root"]
    projects = scan_projects(install)
    templates = scan_templates(install)
    cat = {
        "install": install,
        "projects": projects,
        "template_sets": {k: [os.path.basename(p) for p in v] for k, v in templates.items()},
        "template_paths": templates,
        "settings_presets": sorted({p["settings_preset"] for p in projects
                                    if p.get("settings_preset")}),
    }
    with open(CATALOG, "w", encoding="utf-8") as f:
        json.dump(cat, f, indent=2)
    return cat


def _print_summary(cat):
    print(f"install: {cat['install']}\n")
    print(f"BASE PROJECTS (clonable) — {len(cat['projects'])}:")
    for p in cat["projects"]:
        if p.get("error"):
            print(f"  ! {p['folder']}: {p['error']}")
            continue
        mkt = " / ".join(x for x in (p.get("symbol"), p.get("timeframe")) if x) or "?"
        print(f"  {p['name']:<28} v{p.get('version','?'):<10} "
              f"{p['build_tasks']:>3} build tasks  [{mkt}]")
    print(f"\nTEMPLATE SETS (wirable) — {len(cat['template_sets'])}:")
    for k, v in cat["template_sets"].items():
        print(f"  {k:<28} {len(v):>3} .sqx")
    print(f"\nSETTINGS PRESETS — {len(cat['settings_presets'])}:")
    for s in cat["settings_presets"]:
        print(f"  {s}")
    print(f"\n-> {CATALOG} ({len(cat['projects'])} projects, "
          f"{sum(len(v) for v in cat['template_sets'].values())} templates)")
    if not cat["projects"]:
        print("\nNOTE: no clonable projects found. This skill CLONES an existing project —\n"
              "      create one in SQX once (any build project with a template task), then re-run.")
    if not cat["template_sets"]:
        print("\nNOTE: no strategy templates found under user/settings/StrategyTemplates.\n"
              "      Build some with the sqx-strategy-template skill first.")


if __name__ == "__main__":
    _install = sys.argv[1] if len(sys.argv) > 1 else load_shared_install()
    if not _install:
        raise SystemExit('usage: python engine/discover.py "<install folder>"\n'
                         '(no SQX install stored yet — pass the folder once; it is then '
                         'shared across all sqx-lab skills)')
    _print_summary(discover(_install))
    # discover() already validated; storing here can no longer poison the other skills.
    save_shared_install(_install)
