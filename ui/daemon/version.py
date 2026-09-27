"""Which code a daemon serves: a fingerprint of `ui/daemon/`, so a window can spot a stale one."""

import hashlib
from pathlib import Path

HERE = Path(__file__).parent


def fingerprint() -> str:
    """Hash of every daemon source file's path and modification time.

    Returns:
        Sixteen hex characters. A daemon records it when it starts and a launcher computes
        it from the checkout: when they differ, the daemon still running predates the code
        on disk and lacks whatever routes were added since.
    """
    stamps = sorted(f"{p.relative_to(HERE)}:{p.stat().st_mtime_ns}" for p in HERE.rglob("*.py"))
    return hashlib.sha256("\n".join(stamps).encode()).hexdigest()[:16]
