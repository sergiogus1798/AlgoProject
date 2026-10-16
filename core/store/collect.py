"""Bring a gorilla project's survivors to leaseWeb for step 26 (owner, 2026-10-15, D-1 = A).

Only what step 26 needs, never the whole store: each survivor's folder (its `strategy.sqx` and
the zips beside it), the ledger rows of its asset × timeframe, and what `core.archive` reads of the
project: its `registry.csv` row (appended, install marked `_gorilla`, only if absent) and its
`reports/<P>/` folder and its `harvest/<P>/` (the cosecha the archive freezes as `harvest/`; gorilla keeps
no archive of its own, `_aparte` left out). All come from `source` alone, so `listing` is unchanged. Every name lands with the
`_gorilla` suffix (rule 12) and nothing local is overwritten.

Everything runs here and only reads gorilla over the ssh alias (rsync): `fetch_plans` copies the
manifests and ledger names, `listing` turns them into a plan, `collect` pulls what the plan names.
`portfolio.common.construct.adopt` is the command; it archives what this lands.
"""

import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from core.paths import DATA, MIRRORS

# One ssh connection for every rsync of a collect: one per file tripped gorilla's limit on new
# connections («Connection reset by peer», rsync 255) half-way through a project (📓 2026-10-16).
os.environ.setdefault(
    "RSYNC_RSH",
    "ssh -o ControlMaster=auto -o ControlPath=~/.ssh/cm-%r@%h:%p -o ControlPersist=60",
)
SUFFIX = "_gorilla"
LEDGER = "ledger"


def listing(project: str, data: Path = DATA) -> dict[str, Any]:
    """What gorilla holds for one project: its survivors' folders and the ledger files of their cells."""
    store = data / "store"
    found, ledgers = [], set()
    for manifest in store.glob("*/*/manifest.json"):
        origin = json.loads(manifest.read_text(encoding="utf-8")).get("origin", {})
        if origin.get("project") != project:
            continue
        found.append(f"{manifest.parent.parent.name}/{manifest.parent.name}")
        sym, tf = origin["symbol"], origin["timeframe"]
        for f in (data / LEDGER).glob(f"{sym}_{tf}*.jsonl"):
            if f.name.startswith(f"{sym}_{tf}.") or f.name.startswith(f"{sym}_{tf}_"):
                ledgers.add(f.name)
    return {
        "data": str(data),
        "project": project,
        "folders": sorted(found),
        "ledgers": sorted(ledgers),
    }


def _rsync(src: str, dest: Path, *extra: str) -> None:
    """rsync that never overwrites what is already there; rsync's stderr is shown on failure."""
    cmd = ["rsync", "-a", "--ignore-existing", *extra, src, str(dest)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(e.stderr, file=sys.stderr)
        raise


def _registry(project: str, source: str, dest: Path, dry: bool) -> str:
    """Append gorilla's registry row of the project to the local registry when it has none; never rewrites."""
    mine = dest / "projects" / "registry.csv"
    names = (
        {r["name"] for r in csv.DictReader(mine.open(encoding="utf-8", newline=""))}
        if mine.exists()
        else set()
    )
    if project in names:
        return f"existe    registry: {project}; no se añade"
    if dry:
        return f"traería   registry: {project}"
    tmp = dest / "store" / ".collect-registry.csv"
    try:
        subprocess.run(
            ["rsync", "-a", f"{source}projects/registry.csv", str(tmp)],
            check=True,
            capture_output=True,
        )
        with tmp.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            rows = [r for r in reader if r["name"] == project]
    finally:
        tmp.unlink(missing_ok=True)
    if not rows:
        return f"AVISO     registry: gorilla no tiene fila de {project}"
    row = rows[-1]
    row["install"] += (
        SUFFIX  # a gorilla row never reads as one of this machine's installs
    )
    mine.parent.mkdir(parents=True, exist_ok=True)
    fresh = not mine.exists()
    with mine.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, reader.fieldnames or [])
        if fresh:
            writer.writeheader()
        writer.writerow(row)
    return f"traída    registry: {project} (install {row['install']})"


def collect(
    plan: dict[str, Any], source: str, dest: Path | None = None, dry: bool = False
) -> list[str]:
    """Pull the plan's folders and ledger rows; returns one line per item.

    Args:
        plan: `listing`'s JSON.
        source: where the plan's data root is for rsync — `sqx2:/home/x/AlgoData/` or a local folder.
        dest: the local data root (default: this machine's).
        dry: say what would land, write nothing.
    """
    dest = dest or DATA
    out = []
    local_ids = {  # an identity already held here under any cell is never fetched again
        p.name.rsplit(" ", 1)[-1]
        for p in (dest / "store").glob("*/*")
        if (p / "manifest.json").is_file()
    }
    for rel in plan["folders"]:
        ident = rel.rsplit(" ", 1)[-1]
        target = landing(rel, dest)
        if ident in local_ids and not target.exists():
            out.append(f"ya local  {rel} (misma identidad {ident}); no se trae")
        elif target.exists():
            out.append(f"existe    {target.relative_to(dest)}; no se pisa")
        else:
            if not dry:
                # a sibling temp, renamed only on success: a failed fetch leaves nothing to skip as «existe»
                tmp = target.with_name(f".collect-{target.name}")
                shutil.rmtree(tmp, ignore_errors=True)
                tmp.mkdir(parents=True)
                try:
                    _rsync(f"{source}store/{rel}/", tmp)
                    os.replace(tmp, target)
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)  # gone after the rename
            out.append(
                f"{'traería  ' if dry else 'traída   '} {rel} -> {target.relative_to(dest)}"
            )
    out.append(_registry(plan["project"], source, dest, dry))
    reports = dest / "reports" / plan["project"]
    cosecha = dest / "harvest" / plan["project"]
    if not dry:
        reports.mkdir(parents=True, exist_ok=True)
        _rsync(
            f"{source}reports/{plan['project']}/", reports
        )  # --ignore-existing: resumable
        cosecha.mkdir(parents=True, exist_ok=True)
        _rsync(  # `_aparte` is the whole population set aside, not a harvest: hundreds of MB
            f"{source}harvest/{plan['project']}/", cosecha, "--exclude", "_aparte"
        )
    out.append(
        f"{'traería  ' if dry else 'traídos  '} reports/ y harvest/ de {plan['project']}"
    )
    for name in plan["ledgers"]:
        tmp = dest / "store" / f".collect-{name}"
        mine = dest / LEDGER / (Path(name).stem + SUFFIX + ".jsonl")
        have = (
            set(mine.read_text(encoding="utf-8").splitlines())
            if mine.exists()
            else set()
        )
        if dry:
            out.append(f"traería   ledger {name} -> ledger/{mine.name}")
            continue
        try:
            subprocess.run(
                ["rsync", "-a", f"{source}{LEDGER}/{name}", str(tmp)],
                check=True,
                capture_output=True,
            )
            new = [
                r
                for r in tmp.read_text(encoding="utf-8").splitlines()
                if r and r not in have
            ]
        finally:
            tmp.unlink(missing_ok=True)
        mine.parent.mkdir(parents=True, exist_ok=True)
        with mine.open("a", encoding="utf-8") as fh:
            fh.writelines(r + "\n" for r in new)
        out.append(f"ledger    {mine.name}: {len(new)} filas nuevas")
    return out


def fetch_plans(
    server: str, project: str | None, scratch: Path
) -> list[tuple[dict[str, Any], str]]:
    """Read-only: gorilla's manifests and ledger names into `scratch`, then one plan per project.

    Nothing runs on gorilla (no pull, no code over there): rsync copies the small metadata and
    `listing` reads it here. Returns `(plan, source)` for the project asked, or for every project
    that holds a survivor whose identity this machine holds in no cell of its own — a mirrored
    store is not gorilla's work.
    """
    source = f"{MIRRORS[server]['ssh']}:{DATA.relative_to(Path.home())}/"
    cmd = ["rsync", "-a", "--prune-empty-dirs"]
    for rule in (
        "store/",
        "store/*/",
        "store/*/*/",
        "store/*/*/manifest.json",
        "ledger/",
        "ledger/*.jsonl",
    ):
        cmd += ["--include", rule]
    r = subprocess.run(
        [*cmd, "--exclude", "*", source, f"{scratch}/"], capture_output=True, text=True
    )
    if r.returncode:
        raise RuntimeError(f"no se pudo leer {server} ({source}): {r.stderr.strip()}")
    held = {
        p.name.rsplit(" ", 1)[-1]
        for p in (DATA / "store").glob("*/*")
        if (p / "manifest.json").is_file()
        and not p.name.split(" ")[-2].endswith(SUFFIX)
    }
    names = {
        json.loads(m.read_text(encoding="utf-8"))["origin"]["project"]
        for m in (scratch / "store").glob("*/*/manifest.json")
    }
    plans = [listing(n, scratch) for n in sorted(names) if project in (None, n)]
    if (
        project is None
    ):  # gorilla's own, kept ones: `_gorilla` in the name, never a thrown-away `Test_`
        plans = [
            p
            for p in plans
            if SUFFIX in p["project"]
            and not p["project"].startswith("Test_")
            and any(f.rsplit(" ", 1)[-1] not in held for f in p["folders"])
        ]
    return [(p, source) for p in plans]


def landing(plan_folder: str, dest: Path = DATA) -> Path:
    """Where `collect` lands one of a plan's folders (the `_gorilla` suffixed store folder)."""
    cell, name = plan_folder.split("/")
    base, ident = name.rsplit(" ", 1)
    return dest / "store" / f"{cell}{SUFFIX}" / f"{base}{SUFFIX} {ident}"
