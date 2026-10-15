"""A prop-firm catalogue planted in a temporary data root: shared by the funded tests, not a test itself.

`plant()` must run before anything imports `core.paths` (it sets ALGO_DATA_ROOT, which that module reads
once). The seed in `tests/fixtures/funding/` is the current rows of the two active firms (hantec, ftmo)
at sizes 2000..25000 plus their curated rules, so a test never reads the machine's `AlgoData/funding`.
"""

import atexit
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

SEED = Path(__file__).resolve().parent / "fixtures" / "funding"


def plant() -> Path:
    """Build the catalogue in a fresh temp root, point ALGO_DATA_ROOT at it and return the root.

    Returns:
        The temporary data root; its `funding/` holds firms.yaml, rules/ and funding.sqlite.
    """
    held = sys.modules.get("core.paths")
    if held is not None:
        raise RuntimeError(
            f"core.paths ya se importó con {held.DATA}: planta antes de importar nada del proyecto"
        )
    root = Path(tempfile.mkdtemp(prefix="algo-funding-"))
    atexit.register(shutil.rmtree, root, ignore_errors=True)
    os.environ["ALGO_DATA_ROOT"] = str(root)
    fund = root / "funding"
    shutil.copytree(SEED / "rules", fund / "rules")
    shutil.copy(SEED / "firms.yaml", fund / "firms.yaml")
    from portfolio.funded.catalog import (
        schema,
    )  # after the env var: DB is fixed at import

    db = schema.connect(fund / "funding.sqlite")
    for table, t in json.loads(
        (SEED / "seed.json").read_text(encoding="utf-8")
    ).items():
        marks = ",".join("?" * len(t["cols"]))
        db.executemany(
            f"INSERT INTO {table} ({','.join(t['cols'])}) VALUES ({marks})", t["rows"]
        )
    db.commit()
    db.close()
    return root
