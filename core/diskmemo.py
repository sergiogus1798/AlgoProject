"""What the daemon computed once, kept across restarts: one pickled dict per name in AlgoData/ui/memo/."""

import pickle
from pathlib import Path
from typing import Any

from core.uitoken import FOLDER


def _file(name: str, code: str) -> Path:
    """The memo's file for this code fingerprint: other code starts an empty one, so nothing
    computed by older code is ever served."""
    return FOLDER / "memo" / f"{name}-{code}.pkl"


def load(name: str, code: str) -> dict[Any, Any]:
    """The memo saved under this name by this same code, or an empty one.

    Args:
        name: Which memo («identities», «results»).
        code: Fingerprint of the code that computes it; the caller says what invalidates the memo.

    Returns:
        The dict `save` wrote. Its keys carry each source file's mtime, so an entry of a
        file that changed since is simply never asked for.
    """
    path = _file(name, code)
    return pickle.loads(path.read_bytes()) if path.is_file() else {}


def save(name: str, memo: dict[Any, Any], code: str) -> None:
    """Write the memo, whole and atomically, and drop the ones older code left.

    Args:
        name: Which memo.
        code: As in `load`.
        memo: Keys whose first item is the source file's path; the entries of a file that is
            gone are left out.
    """
    path = _file(name, code)
    path.parent.mkdir(parents=True, exist_ok=True)
    for old in path.parent.glob(f"{name}-*.pkl"):
        if old != path:
            old.unlink()
    alive = {k: v for k, v in memo.items() if Path(k[0]).exists()}
    scratch = path.with_suffix(".tmp")
    scratch.write_bytes(pickle.dumps(alive, protocol=pickle.HIGHEST_PROTOCOL))
    scratch.replace(path)
