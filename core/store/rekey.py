"""Re-key the store after `core.sqxfile.identity` changed: each folder and manifest to the identity its own .sqx has now."""

import csv
import io
import json
import os
import shutil
from collections import defaultdict
from datetime import date
from pathlib import Path

from core import sqxfile
from core.paths import DATA, store_dir
from core.fsio import atomic_write
from core.store.write import MANIFEST, SQX, locked

# The loose tables that name a strategy by identity and are matched later against a fresh one
# (verdict.csv, identity.csv, lineage.csv, tf_mothers.csv…): their identity columns follow the map.
TABLES = ("reports", "raw", "autopilot", "harvest")


def _target(here: Path, new: str) -> Path:
    """The folder `here` becomes: its strategy name and the new identity's 8 letters."""
    return here.with_name(f"{here.name.rsplit(' ', 1)[0]} {new[:8]}")


def plan(
    root: Path, gone: frozenset[Path] = frozenset()
) -> list[tuple[Path, str, str]]:
    """(folder, old identity, new identity) of every stored strategy whose identity moved.

    Raises:
        SystemExit: two stored folders would become one identity (the same strategy saved
            twice in two cells: the owner decides, encargo 76 D), two would share their 8
            letters, or a folder's new name is already taken on disk. Twins in ONE cell are
            `twins`' and `merge`'s (K76b C); `gone` names the folders merge will archive.
    """
    rows = []
    for m in sorted(root.glob(f"*/*/{MANIFEST}")):
        if m.parent in gone:
            continue
        old = json.loads(m.read_text(encoding="utf-8"))["identity"]
        rows.append((m.parent, old, sqxfile.identity(m.parent / SQX)))
    seen: dict[str, Path] = {}
    for here, _, new in rows:
        if new[:8] in seen:
            raise SystemExit(
                f"NO SE REESCRIBE: {seen[new[:8]]} y {here} dan la misma identidad {new[:12]}"
            )
        seen[new[:8]] = here
    moved = [r for r in rows if r[1] != r[2]]
    for here, _, new in moved:
        there = _target(here, new)
        if there != here and there.exists():
            raise SystemExit(f"NO SE REESCRIBE: {here} iría a {there}, que ya existe")
    return moved


def apply(rows: list[tuple[Path, str, str]], backup: Path, out: Path) -> None:
    """Rename each folder to its new 8 letters and rewrite its manifest, one cell lock at a time.

    Args:
        rows: What `plan` returned.
        backup: Every manifest is copied here, under `<cell>/<folder>/`, before it changes.
        out: The old→new map; a folder's row is appended once its rename and manifest are
            written, so a rerun after a crash (which plans only what is left) adds no row twice.
    """
    for here, old, new in rows:
        keep = backup / here.parent.name / here.name / MANIFEST
        keep.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(here / MANIFEST, keep)
        with locked(here.parent):
            there = _target(here, new)
            here.rename(there)
            doc = json.loads((there / MANIFEST).read_text(encoding="utf-8"))
            atomic_write(
                there / MANIFEST,
                json.dumps(
                    {**doc, "identity": new}, ensure_ascii=False, indent=1, default=str
                ).encode(),
                durable=True,
            )
            _record(out, (here.parent.name, here.name, old, new))


def _record(out: Path, row: tuple[str, str, str, str]) -> None:
    """Append one old→new row to the month's map."""
    with out.open("a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if not fh.tell():
            w.writerow(["cell", "folder", "old", "new"])
        w.writerow(row)


def twins(root: Path) -> dict[Path, list[Path]]:
    """{keeper: the other folders of its cell whose .sqx has the same new identity}.

    The keeper is the latest `saved_at`: 🔬 gorilla held 29 such pairs on 2026-10-17, saved
    seconds apart on 2026-10-08/09, and in half of them the older one held more studies.
    """
    groups: dict[tuple[str, str], list[Path]] = defaultdict(list)
    for m in sorted(root.glob(f"*/*/{MANIFEST}")):
        groups[(m.parent.parent.name, sqxfile.identity(m.parent / SQX))].append(
            m.parent
        )
    out = {}
    for folders in groups.values():
        if len(folders) > 1:
            saved = {
                f: json.loads((f / MANIFEST).read_text(encoding="utf-8")).get(
                    "saved_at", ""
                )
                for f in folders
            }
            keeper = max(folders, key=lambda f: (saved[f], f.name))
            out[keeper] = [f for f in folders if f != keeper]
    return out


def merge(groups: dict[Path, list[Path]], backup: Path, out: Path) -> None:
    """Fold each twin into its keeper (owner, K76b C): the keeper gains every study file it
    lacks with its manifest entry and step, keeps its own on a clash, and the twin goes to
    `backup/merged/` with its old identity mapped to the new one."""
    for keeper, others in groups.items():
        with locked(keeper.parent):
            doc = json.loads((keeper / MANIFEST).read_text(encoding="utf-8"))
            new = sqxfile.identity(keeper / SQX)
            for other in others:
                theirs = json.loads((other / MANIFEST).read_text(encoding="utf-8"))
                for name, entry in theirs.get("files", {}).items():
                    if (
                        name not in doc.setdefault("files", {})
                        and (other / name).exists()
                    ):
                        shutil.copy2(other / name, keeper / name)
                        doc["files"][name] = entry
                doc["steps"] = {**theirs.get("steps", {}), **doc.get("steps", {})}
            atomic_write(
                keeper / MANIFEST,
                json.dumps(doc, ensure_ascii=False, indent=1, default=str).encode(),
                durable=True,
            )
            for other in others:
                old = json.loads((other / MANIFEST).read_text(encoding="utf-8"))[
                    "identity"
                ]
                dest = backup / "merged" / other.parent.name / other.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(other), dest)
                _record(out, (other.parent.name, other.name, old, new))


def mapping(root: Path) -> dict[str, str]:
    """Every old→new identity of the store's `identity-map-*.csv`, oldest map first, chains followed."""
    m: dict[str, str] = {}
    for path in sorted(root.glob("identity-map-*.csv")):
        with path.open(encoding="utf-8", newline="") as fh:
            m.update((r["old"], r["new"]) for r in csv.DictReader(fh))
    for old, new in m.items():
        while new in m:
            new = m[new]
        m[old] = new
    return m


def retabled(rows: list[list[str]], m: dict[str, str]) -> tuple[list[list[str]], int]:
    """A CSV's rows with each identity cell (a column named `*identity*` or `mother`) through `m`.

    Returns:
        The rows, and how many cells changed.
    """
    cols = [i for i, h in enumerate(rows[0]) if "identity" in h or h == "mother"]
    n = 0
    for row in rows[1:]:
        for i in cols:
            if i < len(row) and row[i] in m:
                row[i], n = m[row[i]], n + 1
    return rows, n


def tables(m: dict[str, str], dry_run: bool) -> tuple[int, int]:
    """Rewrite through `m` every loose CSV under `TABLES` of the data root that names an old identity.

    Returns:
        (files, cells) changed, or that would change under `dry_run`.
    """
    files = cells = 0
    for path in (p for top in TABLES for p in sorted((DATA / top).rglob("*.csv"))):
        with path.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.reader(fh))
        if not rows:
            continue
        rows, n = retabled(rows, m)
        if not n:
            continue
        files, cells = files + 1, cells + n
        if not dry_run:
            buf = io.StringIO()
            csv.writer(buf, lineterminator="\n").writerows(rows)
            atomic_write(
                path,
                buf.getvalue().encode(),
                seal=not os.access(path, os.W_OK),
                durable=True,
            )
    return files, cells


def _store(root: Path, groups: dict[Path, list[Path]]) -> None:
    """Merge the twins, back up the manifests, re-key the folders and extend the month's map."""
    backup = DATA / "backups" / f"store-rekey-{date.today().isoformat()}"
    out = root / f"identity-map-{date.today():%Y-%m}.csv"
    merge(groups, backup, out)
    apply(plan(root), backup, out)
    print(f"mapa: {out} · copia de los manifiestos: {backup}")


def main(dry_run: bool) -> None:
    """Print the map; unless `dry_run`, back up, write `identity-map-<month>.csv`, re-key, and
    carry every map so far into the loose tables (run it with no workflow running)."""
    root = store_dir()
    groups = twins(root)
    rows = plan(root, frozenset(f for others in groups.values() for f in others))
    print(
        f"{len(rows)} identidades cambian · {len(groups)} carpetas absorben a su gemela"
    )
    if not dry_run and (rows or groups):
        _store(root, groups)
    files, cells = tables(mapping(root), dry_run)
    print(
        f"tablas sueltas: {cells} identidades viejas en {files} CSV"
        + (" (no se tocan)" if dry_run else " reescritas")
    )
