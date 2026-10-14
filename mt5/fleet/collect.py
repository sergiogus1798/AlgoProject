"""Pull the VPS's FleetBeacon files and keep the fleet's live copy, minute history, excursions and health."""

import json
import os
import tempfile
import time
from pathlib import Path

import pandas as pd
import pyarrow as pa

from core.fleetpaths import history_dir, live_dir
from core.paths import DATA
from mt5.fleet import remote, rows

LOG = DATA / "logs" / "fleet-collect.log"
PROBE_EVERY_S = 290  # cron runs every minute; the VPS health is asked about every 5

# Arrow's thread pools abort the interpreter ("terminate called") at exit now and then; a handful of rows needs none.
pa.set_cpu_count(1)
pa.set_io_thread_count(1)


def log(line: str) -> None:
    """Append one timestamped line to the collector's log."""
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")


def write_json(path: Path, obj: dict) -> None:
    """Write a JSON file atomically (temp file, then rename)."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj), encoding="utf-8")
    os.replace(tmp, path)


def append_history(beat: dict) -> bool:
    """Append the beat to its server day's parquet; False when that beat is already the last row."""
    folder = history_dir(beat["login"])
    folder.mkdir(parents=True, exist_ok=True)
    day = folder / f"{rows.server_day(beat)}.parquet"
    kept = pd.read_parquet(day).to_dict("records") if day.exists() else []
    if not rows.is_new(beat, kept[-1]["written_gmt"] if kept else None):
        return False
    pd.DataFrame(kept + [rows.history_row(beat)]).to_parquet(day, index=False)
    excursions = history_dir(beat["login"]) / "excursions.json"
    seen = (
        json.loads(excursions.read_text(encoding="utf-8"))
        if excursions.exists()
        else {}
    )
    write_json(excursions, rows.update_excursions(seen, beat))
    return True


def collect_beats(pulled: Path) -> list[str]:
    """Move each pulled file into the live folder and fold every new beat into its history."""
    notes = []
    for src in sorted(pulled.glob("*.json")):
        dest = live_dir() / src.name
        os.replace(src, dest)
        if not src.name.endswith(".history.json"):
            beat = json.loads(dest.read_text(encoding="utf-8"))
            notes.append(f"{beat['login']}:{'+' if append_history(beat) else '='}")
    return notes


def collect_vps() -> str:
    """Refresh `vps.json` when it is older than PROBE_EVERY_S; say what happened."""
    target = live_dir() / "vps.json"
    if target.exists() and time.time() - target.stat().st_mtime < PROBE_EVERY_S:
        return "vps:fresh"
    health = remote.probe()
    if health is None:
        return "vps:FAIL probe"
    write_json(target, health)
    return "vps:ok"


def main() -> None:
    """One cron pass; a VPS that does not answer leaves the files as they were."""
    live_dir().mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with tempfile.TemporaryDirectory(dir=live_dir()) as tmp:
        if remote.pull(Path(tmp)):
            notes = collect_beats(Path(tmp))
        else:
            log("FAIL pull: the VPS did not answer")
            notes = []
    notes.append(collect_vps())
    log(f"{' '.join(notes)} {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
