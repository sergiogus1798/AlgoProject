"""Every export writes one of these. Without it an export cannot be reproduced or trusted."""

import json
import subprocess
from datetime import date
from pathlib import Path

from core.paths import ROOT


def code_version() -> str:
    """Git commit the current working tree is on.

    Returns:
        Short commit hash, with "-dirty" appended when the tree has uncommitted changes.
    """
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"],
                           capture_output=True, text=True).stdout.strip()
    return head + ("-dirty" if dirty else "")


def write(out_dir: Path, source: dict, command: str, counts: dict) -> Path:
    """Record what produced the files in one export directory.

    Args:
        out_dir: The export directory the manifest describes.
        source: What the data came from, e.g. {"install": ..., "project": ..., "databank": ...}.
        command: The sqcli command or script invocation that produced it, verbatim.
        counts: Row or file counts per artefact, e.g. {"metrics.csv": 231}.

    Returns:
        Path of the manifest written.
    """
    path = out_dir / "manifest.json"
    path.write_text(json.dumps({"date": date.today().isoformat(),
                                "code_version": code_version(),
                                "source": source,
                                "command": command,
                                "counts": counts}, indent=2, default=str), encoding="utf-8")
    return path


def read(out_dir: Path) -> dict:
    """Load the manifest of one export directory.

    Args:
        out_dir: An export directory.

    Returns:
        The parsed manifest.
    """
    return json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
