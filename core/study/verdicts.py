"""A population verdict written where the window and /curate find it: verdict.csv plus its manifest."""

from pathlib import Path

import pandas as pd

from core import manifest

REQUIRED = ("strategy", "identity", "verdict")


def write(out: Path, frame: pd.DataFrame, judged: Path, command: str,
          overrides: list[str], name: str = "verdict.csv") -> Path:
    """Write one verdict table and the manifest that ties it to what it judged.

    Args:
        out: reports/<project>/<databank>/<day>/<module>/.
        frame: One row per strategy, carrying at least strategy, identity and verdict.
        judged: The input it read: an export, a harvest or a work folder.
        command: The command line, verbatim.
        overrides: The --set values it ran with.
        name: The CSV's file name; a module writing two verdicts names the second.

    Returns:
        The CSV's path. The window pairs report and input through the manifest's absolute
        path, never through the folder's date.
    """
    missing = [c for c in REQUIRED if c not in frame.columns]
    if missing:
        raise ValueError(f"verdict table lacks {missing}")
    out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out / name, index=False)
    manifest.write(out, {"input": str(judged.resolve()), "overrides": overrides}, command,
                   {name: len(frame), **frame["verdict"].value_counts().to_dict()})
    return out / name
