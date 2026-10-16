"""The one atomic writer: a file is whole or it is not there, whoever reads it meanwhile."""

import os
import threading
from pathlib import Path


def atomic_write(
    path: Path, data: bytes | str, *, seal: bool = False, durable: bool = False
) -> None:
    """Write a whole file or nothing: a hidden temporary beside it, then renamed over it.

    Args:
        path: The final name; its folders are made.
        data: Bytes, or text (written as utf-8).
        seal: Read-only once written (chmod before the rename, so a cut never leaves a writable final name).
        durable: Flush and fsync before the rename; off for the many small files of a population.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.unlink(missing_ok=True)  # a sealed leftover of a cut write cannot be reopened
    try:
        with tmp.open("wb") as fh:
            fh.write(data.encode() if isinstance(data, str) else data)
            if durable:
                fh.flush()
                os.fsync(fh.fileno())
        if seal:
            tmp.chmod(0o444)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)  # gone already after the replace
