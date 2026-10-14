"""Every export writes one of these. Without it an export cannot be reproduced or trusted."""

import json
import os
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

from core.paths import ROOT

# A truthful record, not an error: exports carried over from AlgoProject_Old predate the
# repository, so no commit can ever name the code that wrote them. The audit accepts this
# marker by name (`tools/daily_audit.manifests_of_unknown_code`) instead of reporting it nightly.
PRE_GIT = "migrated from AlgoProject_Old, pre-git"


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


def write(out_dir: Path, source: dict, command: str, counts: dict,
          since: float | None = None) -> Path:
    """Record what produced the files in one export directory.

    Args:
        out_dir: The export directory the manifest describes.
        source: What the data came from, e.g. {"install": ..., "project": ..., "databank": ...}.
        command: The sqcli command or script invocation that produced it, verbatim.
        counts: Row or file counts per artefact, e.g. {"metrics.csv": 231}.
        since: When the export began reading its sources (`time.time()`); the manifest is dated
            then, so a source changed while the export ran reads as newer than it — stale.

    Returns:
        Path of the manifest written.
    """
    path = out_dir / "manifest.json"
    path.write_text(json.dumps({"date": date.today().isoformat(),
                                "code_version": code_version(),
                                "source": source,
                                "command": command,
                                "counts": counts}, indent=2, default=str), encoding="utf-8")
    if since is not None:
        os.utime(path, (since, since))
    return path


def read(out_dir: Path) -> dict[str, Any]:
    """Load the manifest of one export directory.

    Args:
        out_dir: An export directory.

    Returns:
        The parsed manifest.
    """
    return json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))


def fresh_dir(path: Path) -> Path:
    """Create a folder that did not exist: `path`, or `path` + `_2`, `_3`… when the name is taken.

    Returns:
        The folder created. For an output named by a stamp to the minute: a second run in
        the same minute gets its own folder instead of writing over the first's (OPEN #104-4).
    """
    n, out = 1, path
    while True:
        try:
            out.mkdir(parents=True)
            return out
        except FileExistsError:
            n += 1
            out = path.with_name(f"{path.name}_{n}")
