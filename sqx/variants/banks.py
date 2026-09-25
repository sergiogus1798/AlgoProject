"""The custodian's four variant databanks, emptied off the disk between two batches."""

from core import worker
from core.paths import worker_dir
from sqx.variants import legs as legmod


def clear(cfg: dict) -> int:
    """Empty the input and the three legs' databanks, off the disk, with the install down.

    Args:
        cfg: The `execute` block, with the project.

    Returns:
        How many `.sqx` were deleted. Run after `equity` and `collect`, which read these very
        files, and before the next mother is loaded.

        With the install stopped nothing is in memory, so the next start loads the four
        empty -- hard rule 1 works for us here instead of against us. 🔬 2026-09-25, doing
        it through the API instead cost 206 s and a 47 GB JVM: starting the install syncs
        all 20,000 files INTO memory before `clear` can drop them.
    """
    held = worker.holding(worker_dir(cfg["role"]))
    if held:
        raise SystemExit(f"el {cfg['role']} esta arriba (PID {held}): con SQX vivo un sync "
                         "desharia el borrado. Paralo antes: bin/sqx-worker.sh --role "
                         f"{cfg['role']} stop")
    gone = 0
    for bank in [legmod.source()] + [leg["databank"] for leg in legmod.legs()]:
        for path in legmod.bank_dir(cfg["role"], cfg["project"], bank).glob("*.sqx"):
            path.unlink()
            gone += 1
    return gone
