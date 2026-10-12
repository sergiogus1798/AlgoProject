"""Build the portfolio test root: a second data root for test runs of the real code."""

import argparse
from pathlib import Path

from core import paths

ENV = "ALGO_DATA_ROOT"          # read by `core/paths.py`
REAL = Path(paths._CFG["data_root"]).expanduser()   # the machine's data root, whatever ENV says
ROOT = REAL / "portfolio" / "_test" / "root"
# What a run writes: real folders, empty at first.
WRITABLE = ("ledger", "archive", "portfolio", "reports", "harvest", "barsDerived", "projects", "tmp")
# What a run only reads: links to the real ones. A phase that needs another input adds a line.
LINKS = ("bars", "funding", "projects/registry.csv")
# Segments of the test calendar. The test pool has trades to the end of oos1 and none in oos2;
# a code path that needs a later segment gets oos1's tail under oos2's name with
# `--set calendar.pseudo_oos2_from=<this>`. It is not a holdout: every strategy was chosen on it.
PSEUDO_OOS2_FROM = "2022-01-01"


def build(root: Path = ROOT) -> Path:
    """Create a test root, or complete one that exists; nothing in it is ever overwritten.

    Args:
        root: Where; the module's tests build a throwaway one in a temp folder.

    Returns:
        `root`, holding the WRITABLE folders and each of LINKS as a symlink to the real one.
        ⚠️ A link is read-only by convention only — a write through it lands in the real
        root — so nothing a portfolio run writes is linked.
    """
    for name in WRITABLE:
        (root / name).mkdir(parents=True, exist_ok=True)
    for name in LINKS:
        link = root / name
        if not link.is_symlink():
            link.symlink_to(REAL / name)
    return root


def required() -> None:
    """Refuse to go on when this process writes to the real data root.

    Raises:
        SystemExit: `core.paths.DATA` is the machine's own root — ENV is not set.
    """
    if paths.DATA == REAL:
        raise SystemExit(f"esto solo se ejecuta en una raíz de prueba: {ENV}={ROOT}")


def main(argv: list[str] | None = None) -> None:
    """Build it and print how to run a command under it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="otra raíz que la fija: una desechable con su propio ledger vacío")
    root = parser.parse_args(argv).root.expanduser().resolve()
    if root == REAL or root in REAL.parents:
        raise SystemExit(f"{root} es la raíz real (o la contiene): una raíz de prueba va en otra carpeta")
    print(f"Raíz de prueba: {build(root)}")
    print(f"  escribible: {', '.join(WRITABLE)}")
    print(f"  enlazado (solo lectura): {', '.join(LINKS)}")
    print(f"Para ejecutar un comando en ella: {ENV}={root} python3 -m <módulo> …")


if __name__ == "__main__":
    main()
