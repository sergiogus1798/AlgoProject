"""What the daemon computed once, kept across restarts: one pickled dict per name in AlgoData/ui/memo/."""

from typing import Any
import pickle
from pathlib import Path

from core import sqxfile
from core.uitoken import FOLDER
from ui.daemon import version


def _file(name: str) -> Path:
    """The memo's file for the code on disk: another daemon or `core/sqxfile.py` version starts
    an empty one, so nothing computed by older code is ever served."""
    code = f"{version.fingerprint()}{Path(sqxfile.__file__).stat().st_mtime_ns}"
    return FOLDER / "memo" / f"{name}-{code}.pkl"


def load(name: str) -> dict[Any, Any]:
    """The memo saved under this name by this same code, or an empty one.

    Args:
        name: Which memo («identities», «results»).

    Returns:
        The dict `save` wrote. Its keys carry each source file's mtime, so an entry of a
        file that changed since is simply never asked for.
    """
    path = _file(name)
    return pickle.loads(path.read_bytes()) if path.is_file() else {}


def save(name: str, memo: dict[Any, Any]) -> None:
    """Write the memo, whole and atomically, and drop the ones older code left.

    Args:
        name: Which memo.
        memo: Keys whose first item is the source file's path; the entries of a file that is
            gone are left out.
    """
    path = _file(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    for old in path.parent.glob(f"{name}-*.pkl"):
        if old != path:
            old.unlink()
    alive = {k: v for k, v in memo.items() if Path(k[0]).exists()}
    scratch = path.with_suffix(".tmp")
    scratch.write_bytes(pickle.dumps(alive, protocol=pickle.HIGHEST_PROTOCOL))
    scratch.replace(path)
