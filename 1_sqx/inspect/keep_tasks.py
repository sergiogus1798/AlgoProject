#!/usr/bin/env python3
"""Produce a variant of a project.cfx keeping only tasks of the given types.

The sqx-strategy-project skill clones a donor's build task per template but
carries the donor's remaining task chain along. For a builder-only project the
rest has to go - together with the task XML members and the databank
registrations nothing references any more.

    python3 keep_tasks.py in.cfx out.cfx --types Build [--keep-databanks A,B]

System databanks (the first `--system-count` by position, default 5) are always
kept; SQX expects them to exist.
"""
import argparse, os, shutil, sys, tempfile, zipfile
import xml.etree.ElementTree as ET


def main() -> None:
    """Copy a .cfx keeping only the chosen task types, their XML members and databanks."""
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--types", default="Build",
                    help="comma-separated task types to KEEP (default: Build)")
    ap.add_argument("--system-count", type=int, default=5,
                    help="how many lowest-position databanks are system ones")
    args = ap.parse_args()
    keep_types = {t.strip() for t in args.types.split(",") if t.strip()}

    with zipfile.ZipFile(args.src) as z:
        members = {n: z.read(n) for n in z.namelist()}

    cfg = ET.fromstring(members["config.xml"])
    tasks_el = cfg.find("Tasks")
    all_tasks = list(tasks_el.findall("Task"))

    kept, dropped = [], []
    for t in all_tasks:
        (kept if t.get("type") in keep_types else dropped).append(t)
    if not kept:
        sys.exit(f"nothing kept - no task of type(s) {sorted(keep_types)}")
    for t in dropped:
        tasks_el.remove(t)

    # task XML members referenced only by dropped tasks go too
    kept_files = {t.get("taskXMLFile") for t in kept}
    dropped_files = {t.get("taskXMLFile") for t in dropped} - kept_files

    # databanks: keep the system ones plus anything a kept task still writes
    referenced = set()
    for t in kept:
        try:
            sub = ET.fromstring(members[t.get("taskXMLFile")])
        except Exception:
            continue
        for d in sub.findall("Databanks/Databank"):
            v = d.get("value")
            if v and v != "null":
                referenced.add(v)

    dbs_el = cfg.find("Databanks")
    dbs = list(dbs_el.findall("Databank"))
    by_pos = sorted(dbs, key=lambda d: int(d.get("position") or 0))
    system = {d.get("name") for d in by_pos[:args.system_count]}
    dropped_dbs = []
    for d in dbs:
        if d.get("name") not in system and d.get("name") not in referenced:
            dbs_el.remove(d)
            dropped_dbs.append(d.get("name"))

    members["config.xml"] = ET.tostring(cfg, encoding="utf-8", xml_declaration=True)
    for f in dropped_files:
        members.pop(f, None)

    os.makedirs(os.path.dirname(os.path.abspath(args.dst)) or ".", exist_ok=True)
    with zipfile.ZipFile(args.dst, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in members.items():
            z.writestr(n, data)

    print(f"kept {len(kept)} task(s): " + ", ".join(t.get("type") for t in kept))
    print(f"dropped {len(dropped)} task(s): " +
          ", ".join(sorted({t.get('type') for t in dropped})))
    print(f"dropped {len(dropped_files)} task XML member(s)")
    print(f"kept databanks: " + ", ".join(d.get("name") for d in dbs_el.findall("Databank")))
    if dropped_dbs:
        print(f"dropped {len(dropped_dbs)} unreferenced databank(s): " + ", ".join(dropped_dbs))
    print(f"-> {args.dst}")


if __name__ == "__main__":
    main()
