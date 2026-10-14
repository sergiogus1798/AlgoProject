"""The one root of a monkey run: every subprocess of it is handed the same `--seed` (encargo 66 §1.5, D2)."""

import json
import os
import tempfile
from datetime import date

import numpy as np

from core.paths import report_dir

FILE = ".seed"  # `<FILE>-<databank>-<day>` beside the databank folders: a file, so results.hits never lists it


def root(project: str, databank: str) -> int:
    """The root the monkeys of this databank's report folder draw from today.

    Args:
        project: Project name.
        databank: Databank name.

    Returns:
        The `seed` of the folder's manifest when a run already wrote one; else the root kept
        in the `.seed` file beside the databank folders; else a fresh 32-bit root, linked there
        whole (first writer wins, a loser reads the winner's), with no `monkey/` folder made.
    """
    out = report_dir(project, databank, date.today().isoformat())
    manifest = out / "monkey" / "manifest.json"
    if manifest.exists():
        seed = (
            json.loads(manifest.read_text(encoding="utf-8"))
            .get("source", {})
            .get("seed")
        )
        if seed is not None:
            return int(seed)
    kept = out.parent.with_name(f"{FILE}-{out.parent.name}-{out.name}")
    kept.parent.mkdir(parents=True, exist_ok=True)
    seed = int(np.random.SeedSequence().generate_state(1)[0])
    fd, tmp = tempfile.mkstemp(dir=kept.parent, prefix=FILE)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(str(seed))
        os.link(tmp, kept)  # atomic, complete or absent: the first writer wins
    except FileExistsError:
        pass
    finally:
        os.unlink(tmp)
    return int(kept.read_text(encoding="utf-8"))
