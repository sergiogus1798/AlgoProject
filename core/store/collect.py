"""Bring a gorilla project's survivors to leaseWeb for step 26 (owner, 2026-10-15, D-1 = A).

Only what step 26 needs, never the whole store: each survivor's folder (its `strategy.sqx` and
the zips beside it) and the ledger rows of its asset × timeframe. Every name lands with the
`_gorilla` suffix (rule 12) and nothing local is overwritten.

Two halves: `listing` runs ON gorilla through `bin/remote.sh` (read-only) and prints JSON;
`collect` runs here and pulls what that JSON names with rsync over the ssh alias.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from core.paths import DATA, MIRRORS, ROOT

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


def _rsync(src: str, dest: Path) -> None:
    """rsync that never overwrites what is already there; rsync's stderr is shown on failure."""
    cmd = ["rsync", "-a", "--ignore-existing", src, str(dest)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(e.stderr, file=sys.stderr)
        raise


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
        cell, name = rel.split("/")
        base, ident = name.rsplit(" ", 1)
        target = dest / "store" / f"{cell}{SUFFIX}" / f"{base}{SUFFIX} {ident}"
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


def main(argv: list[str]) -> int:
    """`list <project>` (on gorilla) · `<server> <project> [--dry-run]` (here, via bin/remote.sh)."""
    if argv and argv[0] == "list":
        print(json.dumps(listing(argv[1])))
        return 0
    if len(argv) < 2 or argv[0] not in MIRRORS:
        print(
            "uso: bin/remote.sh gorilla collect <PROYECTO> [--dry-run]", file=sys.stderr
        )
        return 2
    server, project, dry = argv[0], argv[1], "--dry-run" in argv
    r = subprocess.run(
        [
            str(ROOT / "bin" / "remote.sh"),
            server,
            "python3",
            "-m",
            "core.store.collect",
            "list",
            project,
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode:
        print(r.stderr.strip() or r.stdout.strip(), file=sys.stderr)
        return r.returncode
    lines = r.stdout.strip().splitlines()
    if not lines:
        raise RuntimeError(f"{server} returned no listing for {project}")
    plan = json.loads(lines[-1])
    if not plan["folders"]:
        print(f"{server}: ningún superviviente guardado de {project}", file=sys.stderr)
        return 1
    source = f"{MIRRORS[server]['ssh']}:{plan['data']}/"
    print("\n".join(collect(plan, source, dry=dry)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
