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
import argparse, os, sys, zipfile
import xml.etree.ElementTree as ET


def keep(members: dict[str, bytes], keep_types: set[str], system_count: int = 5,
         only: set[str] | None = None) -> tuple[dict[str, bytes], dict]:
    """Strip a project's contents down to the chosen task types.

    Args:
        members: The .cfx contents by member name, as read from the archive.
        keep_types: Task types to keep, e.g. {"Build"}.
        system_count: How many lowest-position databanks are system ones. SQX expects
            those to exist whatever the project does, so they are never dropped.
            only: Task XML file names to narrow the kept types down to. The donor's chain
            holds fourteen Retest tasks; a study that only needs the IS→OOS gate wants
            one of them, and which one is not a property of the type.

    Returns:
        The rewritten members, and a summary naming what was kept and dropped. Raises
        SystemExit when no task survives, which means the type was misspelled.
    """
    cfg = ET.fromstring(members["config.xml"])
    tasks_el = cfg.find("Tasks")

    kept, dropped = [], []
    for t in list(tasks_el.findall("Task")):
        wanted = t.get("type") in keep_types and (not only or t.get("taskXMLFile") in only)
        (kept if wanted else dropped).append(t)
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
    by_pos = sorted(dbs_el.findall("Databank"), key=lambda d: int(d.get("position") or 0))
    system = {d.get("name") for d in by_pos[:system_count]}
    dropped_dbs = []
    for d in list(dbs_el.findall("Databank")):
        if d.get("name") not in system and d.get("name") not in referenced:
            dbs_el.remove(d)
            dropped_dbs.append(d.get("name"))

    members = dict(members)
    members["config.xml"] = ET.tostring(cfg, encoding="utf-8", xml_declaration=True)
    for f in dropped_files:
        members.pop(f, None)

    return members, {"kept": [t.get("type") for t in kept],
                     "dropped": sorted({t.get("type") for t in dropped}),
                     "dropped_files": len(dropped_files),
                     "databanks": [d.get("name") for d in dbs_el.findall("Databank")],
                     "dropped_databanks": dropped_dbs}


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

    with zipfile.ZipFile(args.src) as z:
        members = {n: z.read(n) for n in z.namelist()}

    members, done = keep(members, {t.strip() for t in args.types.split(",") if t.strip()},
                         args.system_count)

    os.makedirs(os.path.dirname(os.path.abspath(args.dst)) or ".", exist_ok=True)
    with zipfile.ZipFile(args.dst, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in members.items():
            z.writestr(n, data)

    print(f"kept {len(done['kept'])} task(s): " + ", ".join(done["kept"]))
    print(f"dropped task(s): " + ", ".join(done["dropped"]))
    print(f"dropped {done['dropped_files']} task XML member(s)")
    print("kept databanks: " + ", ".join(done["databanks"]))
    if done["dropped_databanks"]:
        print(f"dropped {len(done['dropped_databanks'])} unreferenced databank(s): "
              + ", ".join(done["dropped_databanks"]))
    print(f"-> {args.dst}")


if __name__ == "__main__":
    main()
