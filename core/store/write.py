"""Write into a strategy's folder so that a cut leaves it as it was or as it will be, never half.

On disk: `store/<cell>/<identity>/` — a cell is asset × timeframe × template, and every run of a
cell saves into the same cell folder (owner, 2026-10-08); `store/<cell>/runs.json` lists them.
"""

import fcntl
import hashlib
import io
import json
import os
import threading
import time
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from core import sqxfile
from core.paths import store_dir

SQX, MANIFEST, RUNS = "strategy.sqx", "manifest.json", "runs.json"
POOL = ".pool"          # store/<cell>/.pool/<sha256>.zip: every zip's bytes, once per cell
_HELD = threading.local()        # per THREAD: the cells it holds the lock of (flock alone does not tell threads apart)
EPOCH = (2000, 1, 1, 0, 0, 0)   # every zip member's date: the same content gives the same bytes


def folder(identity: str, cell: str = "", name: str = "") -> Path:
    """The strategy's folder inside its cell: `<its name> <first 8 of its identity>`.

    Args:
        identity: The strategy.
        cell: Where to put it when it is not stored yet; a stored one is found wherever it is.
        name: Its name in SQX, for a new one (owner, 2026-10-08: a folder he can find by eye;
            the 8 letters keep apart the names SQX reuses from one build to the next).
    """
    held = _held().get(identity[:8])
    if held is not None and not held.exists():      # gone within the same clock tick as the listing
        _SEEN.clear()
        held = _held().get(identity[:8])
    return held or store_dir() / (cell or "_") / f"{name or '_'} {identity[:8]}"


_SEEN: dict = {}        # store root -> (signature, {first 8 of identity: folder}, time of the listing)


def _held() -> dict[str, Path]:
    """Every stored folder by the 8 letters it ends in, listed again only when a cell folder changed.

    A strategy folder appearing, going or being renamed changes its cell folder's mtime, so the
    signature (the root's and every cell's) tells when the dictionary is stale.
    """
    root = store_dir()
    cells = sorted((e for e in os.scandir(root) if e.is_dir() and not e.name.startswith(".")), key=lambda e: e.name) if root.is_dir() else []
    sign = (root.stat().st_mtime_ns if cells else 0, tuple((e.name, e.stat().st_mtime_ns) for e in cells))
    newest, seen = max([sign[0], *(m for _, m in sign[1])]), _SEEN.get(root, (None, {}, 0))
    young = seen[2] - newest < 1_000_000_000    # listed within a clock tick of the newest mtime: a folder made later in that tick leaves it as it was
    if young or seen[0] != sign:
        held: dict[str, Path] = {}
        for cell in cells:
            for e in os.scandir(cell.path):
                if not e.name.startswith(".") and " " in e.name:
                    held.setdefault(e.name.rsplit(" ", 1)[1], Path(e.path))
        _SEEN[root] = (sign, held, time.time_ns())
    return _SEEN[root][1]


def atomic(path: Path, data: bytes, seal: bool = True) -> None:
    """Write a whole file or nothing: a hidden temporary beside it, flushed to disk, then renamed.

    Args:
        path: The final name.
        data: Its bytes.
        seal: Read-only once written; only the manifest is ever rewritten.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.unlink(missing_ok=True)      # a sealed leftover of a cut write cannot be reopened
    with tmp.open("wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    if seal:                 # before the rename: a cut never leaves a final name writable
        tmp.chmod(0o444)
    os.replace(tmp, path)


@contextmanager
def locked(cell: Path) -> Iterator[None]:
    """One writer at a time per cell: every manifest and `runs.json` is read, changed, rewritten.

    Two saves of one cell at once lost half of what they wrote (reviewed 2026-10-08); the lock
    is a file of the cell, held for the length of one change and re-entrant inside a thread.
    """
    mine = _HELD.__dict__.setdefault("cells", set())
    if cell in mine:
        yield
        return
    cell.mkdir(parents=True, exist_ok=True)
    with (cell / ".lock").open("w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        mine.add(cell)
        try:
            yield
        finally:
            mine.discard(cell)


def manifest(identity: str) -> dict[str, Any]:
    """The strategy's manifest, {} when it was never saved."""
    path = folder(identity) / MANIFEST
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def record(identity: str, doc: dict) -> None:
    """Rewrite the manifest whole — the one file of a folder that changes."""
    atomic(folder(identity) / MANIFEST,
           json.dumps(doc, ensure_ascii=False, indent=1, default=str).encode(), seal=False)


def put_sqx(sqx: Path, cell: str, origin: dict) -> str:
    """Save the strategy file, once, and open its manifest.

    Args:
        sqx: The .sqx to save.
        cell: Its cell's folder name, e.g. `USDJPY_M30_doubleROCLong`.
        origin: Where it comes from (project, name, symbol, timeframe, template...).

    Returns:
        Its identity. The stored copy is read back and must carry that identity, or this raises:
        a file that cannot be read back was not saved. A strategy already stored is left alone.
    """
    identity = sqxfile.identity(sqx)
    target = folder(identity, cell, origin.get("strategy", "")) / SQX
    with locked(target.parent.parent):
        if not target.exists() or not _carries(target, identity):   # a damaged copy is replaced
            atomic(target, sqx.read_bytes())
            _SEEN.clear()
        if not _carries(target, identity):
            raise OSError(f"{target}: lo guardado no tiene la identidad {identity[:12]}")
        if not manifest(identity):
            record(identity, {"identity": identity, "cell": cell, "origin": origin,
                              "saved_at": datetime.now().isoformat(timespec="seconds"),
                              "files": {}, "steps": {}})
    return identity


def _carries(path: Path, identity: str) -> bool:
    """Whether a stored .sqx opens and has this identity."""
    try:
        return sqxfile.identity(path) == identity
    except (zipfile.BadZipFile, KeyError, OSError):
        return False


def packed(source: Path) -> bytes:
    """A folder as one zip, members sorted and dated EPOCH so equal content is equal bytes."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(p for p in source.rglob("*") if p.is_file()):
            z.writestr(zipfile.ZipInfo(path.relative_to(source).as_posix(), EPOCH),
                       path.read_bytes(), zipfile.ZIP_DEFLATED, 9)
    return buf.getvalue()


def pooled(path: Path, data: bytes, digest: str) -> None:
    """Give `path` these bytes as a hard link to the cell's pool, where equal bytes live once.

    A population file is the same for every strategy of a run: each folder still holds it —
    copying a folder elsewhere carries everything — and the disk pays for it once (owner,
    2026-10-08). A pool file nobody links any more (`st_nlink == 1`) is garbage after a purge.
    """
    blob = path.parent.parent / POOL / f"{digest}.zip"
    blob.parent.mkdir(exist_ok=True)
    if not blob.exists() or hashlib.sha256(blob.read_bytes()).hexdigest() != digest:
        atomic(blob, data)
    os.link(blob, path)


def add(identity: str, stem: str, source: Path, about: dict) -> str:
    """Add one set of tests to a stored strategy as `<stem>.zip`.

    Args:
        identity: The strategy; its .sqx is already stored.
        stem: The file's name without `.zip`, e.g. `gate.Results.2026-10-07`.
        source: The folder holding everything of that set of tests about this strategy.
        about: What the manifest says of the file (study, databank, day, config_hash...).

    Returns:
        The file's name. The same content again is the same file and nothing is written; a
        different content under a taken name becomes `<stem>.2.zip`, `.3`… — a test repeated
        under new criteria never overwrites the old one. The file is written before the
        manifest names it, so a cut in between leaves an orphan the next save adopts.
    """
    data = packed(source)
    digest = hashlib.sha256(data).hexdigest()
    with locked(folder(identity).parent):
        doc, n = manifest(identity), 1
        while True:
            name = f"{stem}.zip" if n == 1 else f"{stem}.{n}.zip"
            path = folder(identity) / name
            if not path.exists():
                pooled(path, data, digest)
                break
            if hashlib.sha256(path.read_bytes()).hexdigest() == digest:
                break
            n += 1
        if doc["files"].get(name, {}).get("sha256") != digest:
            doc["files"][name] = {"sha256": digest, "bytes": len(data),
                                  "added_at": datetime.now().isoformat(timespec="seconds"), **about}
            record(identity, doc)
    return name


def step(identity: str, n: str, row: dict) -> None:
    """Note what one workflow step said of the strategy: verdict, outcome, reason and the run.

    A failed step is marked here and nothing is deleted (owner, 2026-10-08): the folder stays
    until he purges it.
    """
    with locked(folder(identity).parent):
        doc = manifest(identity)
        if doc["steps"].get(n) != row:
            doc["steps"][n] = row
            record(identity, doc)


def run(cell: str, project: str, about: dict) -> None:
    """Note one run of a cell in its `runs.json`: how many it generated and how many survived.

    The sum of `generated` over a cell's runs is the denominator its stored strategies came from.
    """
    path = store_dir() / cell / RUNS
    with locked(path.parent):
        runs = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if runs.get(project) != about:
            runs[project] = about
            atomic(path, json.dumps(runs, ensure_ascii=False, indent=1).encode(), seal=False)
