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
import hashlib
import io
import json
from pathlib import Path

import yaml

from core.paths import DATA, ROOT

REMOTE = DATA / "ledger" / "_remote"
_DROP = ("id", "host")  # added by the writer; never part of what a row says
_TIME = ("ts", "at", "date")  # L1 / campaign / judgements rows carry one of these


def server() -> str:
    """This machine's server name: `server:` in config/machine.yaml, `leaseWeb` when absent.

    gorilla's machine.yaml says `server: gorilla`; the name is the suffix of every shard.
    """
    cfg = yaml.safe_load((ROOT / "config" / "machine.yaml").read_text(encoding="utf-8"))
    return str(cfg.get("server") or "leaseWeb")


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


def _places(path: Path) -> list[Path]:
    """Legacy file, this server's shard, then every pulled remote file (legacy and shards)."""
    out = [path, shard_path(path)]
    rel = path.relative_to(DATA)
    for folder in sorted(REMOTE.glob("*/")) if REMOTE.exists() else []:
        if not folder.is_dir():
            continue
        base = folder / rel
        out += [base, *sorted(base.parent.glob(f"{base.stem}.*{base.suffix}"))]
    return list(dict.fromkeys(out))


def _lines(file: Path) -> list[str]:
    """Non-empty lines of a ledger file; a CSV loses its header. Missing file: none."""
    if not file.exists():
        return []
    text = file.read_text(encoding="utf-8")
    if file.suffix != ".csv":
        return [x for x in text.splitlines() if x.strip()]
    # a CSV row is a line too, but the header is not a row
    return [x for x in text.splitlines()[1:] if x.strip()]


def read_all(path: Path) -> list[dict]:
    """Deduplicated union of a ledger file's legacy, local-shard and pulled-remote rows.

    Args:
        path: The legacy (unsuffixed) file under the data root, e.g. `study.path(study)`.

    Returns:
        Rows as dicts, first occurrence kept, stably ordered by `ts`/`at`/`date` when they carry
        one (rows without keep their place). `.csv` rows are dicts of strings.
    """
    seen: set[str] = set()
    rows: list[dict] = []
    for file in _places(path):
        if file.suffix == ".csv" and file.exists():
            head = file.read_text(encoding="utf-8").splitlines()[0]
            names = next(csv.reader([head]))
        for line in _lines(file):
            rid = row_id(line)
            if rid in seen:
                continue
            seen.add(rid)
            rows.append(
                next(csv.DictReader(io.StringIO(line), names))
                if file.suffix == ".csv"
                else json.loads(line)
            )

    def when(r: dict) -> str:
        """The row's time string, empty when it has none."""
        return next((str(r[k]) for k in _TIME if r.get(k)), "")

    return sorted(rows, key=when)  # stable: undated rows sort first, in input order
