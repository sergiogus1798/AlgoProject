"""Everything one run of the retest study reads from one ingest, assembled once."""

from core import manifest
from studies.breakage.mcRetest.measure import store


def load(project: str, databank: str, day: str) -> dict:
    """The inputs one.run() and many.run() read.

    Args:
        project: SQX project the eight task databanks belong to.
        databank: The ingest's name, MCR_All by default.
        day: The ingest's date.

    Returns:
        {"keys", "sims", "original", "levels", "provenance", "identity", "trades", "asset",
        "folder"}. Identity comes from the ingest's manifest, which records it since
        2026-09-25; an older ingest reads None. `trades` is None and `asset` is None on an
        ingest written before 2026-09-29 (OPEN.md #71), which `run.battery()` reads as "no
        footprint to benchmark against" rather than a crash.
    """
    keys = {"project": project, "databank": databank, "day": day}
    folder = store.root(**keys)
    source = manifest.read(folder)["source"]
    provenance = source["tasks"]
    identity = {key.split("/", 1)[1]: entry.get("identity")
                for key, entry in provenance.items() if key.startswith("stress/")}
    trades = store.load_trades(**keys) if (folder / store.TRADES).exists() else None
    return {"keys": keys, "sims": store.load_sims(**keys),
            "original": store.load_original(**keys), "levels": store.load_levels(**keys),
            "provenance": provenance, "identity": identity, "trades": trades,
            "asset": source.get("asset"), "folder": folder}
