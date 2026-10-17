"""Ledger shards (D27, option A): one writer per file, the union read back deduplicated.

Each server appends only to its own shard, `<stem>.<server>.<ext>` beside the legacy file, and
`bin/ledger-pull.sh <server>` copies the other server's files (legacy and shard) under
`ledger/_remote/<server>/`, mirroring their path relative to the data root. `read_all` is the
union of the four places a ledger file can live, deduplicated by `row_id`: pulling twice, or a row
present in a legacy file and in a shard, counts once. Pure functions, no writes.

`.jsonl` files give dicts (parsed lines). `.csv` files give dicts too (`csv.DictReader`), which is
right for the append-only `judgements.csv`; `projects.csv` is a table rewritten whole, keyed by
project, so its union is NOT a plain dedup: the phase-2 reader must pick, per key, the newest row.
"""

import csv
import functools
import hashlib
import heapq
import io
import json
import uuid
from pathlib import Path
from typing import Any

import yaml

from core.paths import DATA, ROOT

REMOTE = DATA / "ledger" / "_remote"
_DROP = ("id", "host")  # added by the writer; never part of what a row says
_TIME = ("ts", "at", "date")  # L1 / campaign / judgements rows carry one of these


@functools.cache
def server() -> str:
    """This machine's server name, the suffix of every shard it writes.

    `server:` in config/machine.yaml when set; otherwise by what the file already says: the head
    machine (leaseWeb) is the one that lists `mirrors:`, and a machine that lists none is a mirror
    (gorilla's machine.yaml is read-only for us and carries neither key).
    """
    cfg = yaml.safe_load((ROOT / "config" / "machine.yaml").read_text(encoding="utf-8"))
    # ponytail: one mirror exists; a second would need its own `server:` key
    return str(cfg.get("server") or ("leaseWeb" if cfg.get("mirrors") else "gorilla"))


def shard_path(path: Path, host: str = "") -> Path:
    """`<stem>.<host>.<ext>` beside `path`; host defaults to this machine."""
    return path.with_name(f"{path.stem}.{host or server()}{path.suffix}")


def row_id(line: str) -> str:
    """Hash of a row's content: the same for a legacy line and for the row with `id`/`host` added."""
    line = line.strip()
    try:
        row = json.loads(line)
        if isinstance(row, dict):
            row = {k: v for k, v in row.items() if k not in _DROP}
            line = json.dumps(row, sort_keys=True, separators=(",", ":"), default=str)
    except ValueError:
        pass  # a CSV line, or a torn one: its own text is the content
    return hashlib.sha1(line.encode("utf-8")).hexdigest()[:16]


def stamp(row: dict[str, Any]) -> str:
    """The JSON line a writer appends to its shard: the row plus its `id` and this `host`."""
    row_ = {k: v for k, v in row.items() if k not in _DROP}
    # a per-row nonce, not a content hash: two genuine identical searches in one second stay two
    return json.dumps(
        {**row_, "id": uuid.uuid4().hex[:16], "host": server()}, default=str
    )


def _remote_copies(path: Path) -> list[Path]:
    """Where each pulled server holds `path`; none for a path outside the data root."""
    try:
        rel = path.relative_to(DATA)
    except ValueError:
        return []
    folders = sorted(REMOTE.glob("*/")) if REMOTE.exists() else []
    return [f / rel for f in folders if f.is_dir()]


def stems(folder: Path) -> list[str]:
    """Sorted names of the `.jsonl` files in `folder` and in its pulled copies, shard suffix dropped."""
    found = [*folder.glob("*.jsonl")]
    for remote in _remote_copies(folder):
        found += remote.glob("*.jsonl")
    return sorted({f.stem.split(".")[0] for f in found})


def _places(path: Path) -> list[Path]:
    """Legacy file, this server's shard, then every pulled remote file (legacy and shards)."""
    out = [path, shard_path(path)]
    for base in _remote_copies(path):
        out += [base, *sorted(base.parent.glob(f"{base.stem}.*{base.suffix}"))]
    return list(dict.fromkeys(out))


def _lines(file: Path) -> list[str]:
    """Non-empty lines of a ledger file; a CSV loses its header. Missing or empty file: none."""
    if not file.exists():
        return []
    text = file.read_text(encoding="utf-8")
    if file.suffix != ".csv":
        return [x for x in text.splitlines() if x.strip()]
    # a CSV row is a line too, but the header is not a row
    return [x for x in text.splitlines()[1:] if x.strip()]


def _when(r: dict) -> str:
    """The row's time string, empty when it has none."""
    return next((str(r[k]) for k in _TIME if r.get(k)), "")


def _union(path: Path) -> list[tuple[str, dict]]:
    """(key, row) of the union, deduplicated, per-file append order kept, local files first.

    A stamped row (`id`, a nonce) is the same row as another with that id; an unstamped (legacy)
    row is the same as another with equal content, and as a stamped row of equal content from
    another file (a copy). Across files the rows are merged by time only when every row has one.
    """
    seen: set[str] = set()
    stamped: set[str] = set()  # content of stamped rows
    plain: set[str] = set()  # content of unstamped rows
    per_file: list[list[tuple[str, dict]]] = []
    for file in _places(path):
        lines = _lines(file)
        if not lines:
            continue
        if file.suffix == ".csv":
            names = next(csv.reader([file.read_text(encoding="utf-8").splitlines()[0]]))
        mine: list[tuple[str, dict]] = []
        for line in lines:
            row = (
                next(csv.DictReader(io.StringIO(line), names))
                if file.suffix == ".csv"
                else json.loads(line)
            )
            content = row_id(line)
            key = f"id:{row['id']}" if isinstance(row, dict) and row.get("id") else ""
            if key:
                if key in seen or content in plain:
                    continue
                stamped.add(content)
            else:
                key = content
                if key in plain or key in stamped:
                    continue
                plain.add(content)
            seen.add(key)
            mine.append((key, row))
        per_file.append(mine)
    flat = [x for f in per_file for x in f]
    if flat and all(_when(r) for _, r in flat):
        return list(heapq.merge(*per_file, key=lambda x: _when(x[1])))
    return flat


def digest(path: Path) -> str | None:
    """SHA-256 of the union's row keys (order does not matter); None when it is empty."""
    keys = sorted(k for k, _ in _union(path))
    return hashlib.sha256("\n".join(keys).encode()).hexdigest() if keys else None


def files(path: Path) -> list[Path]:
    """The existing files of the union, for a cheap raw-text test."""
    return [f for f in _places(path) if f.exists()]


def mtime(path: Path) -> float:
    """Latest modification time among the files of the union; 0 when none exists."""
    return max((f.stat().st_mtime for f in files(path)), default=0.0)


def read_all(path: Path) -> list[dict]:
    """Deduplicated union of a ledger file's legacy, local-shard and pulled-remote rows.

    Args:
        path: The legacy (unsuffixed) file under the data root, e.g. `study.path(study)`.

    Returns:
        Rows as dicts, each file in its append order. When every row carries `ts`/`at`/`date` the
        files are merged by it; otherwise they are concatenated, this machine's first. A row
        counts once by its `id`; a row without one (legacy) once by content. `.csv` rows are dicts
        of strings.
    """
    return [row for _, row in _union(path)]
