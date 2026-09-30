"""What of a databank is loaded, what is stale, and the commands that bring it up to date."""

import base64
import hashlib
import re
import struct
import zipfile
from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree

from core import sqxstats
from core.paths import export_dir, harvest_dir, metrics_export
from ui.daemon import jobs
from ui.daemon.loader import find

# The three products a databank's page reads, by what they unlock on screen.
PIECES = {"metrics": "métricas de cada estrategia (se leen del .sqx, sin SQX)",
          "trades": "operaciones una a una (orderstocsv en el conductor)",
          "harvest": "cosecha IS+OOS emparejada: la Ficha y la puerta (orderstocsv en el conductor)"}


def newest(folder: Path, pattern: str) -> Path | None:
    """The newest dated export under a folder: `<day>/<pattern>`.

    Args:
        folder: `raw/<P>/<D>` or `harvest/<P>/<D>`.
        pattern: The file whose presence makes a day complete, e.g. `manifest.json`.

    Returns:
        That file in the newest complete day, or None.
    """
    days = sorted(d for d in folder.glob("*") if (d / pattern).exists()) if folder.is_dir() else []
    return days[-1] / pattern if days else None


JAVA_REF = re.compile(r"^([\w.$]+)@[0-9a-f]+$")


def _records(blob: str) -> bytes:
    """A statistics blob's records, sorted: the same statistics whatever order SQX wrote."""
    raw, out, i = base64.b64decode(blob), [], 0
    while i < len(raw):
        kind, start = raw[i], i
        if kind > sqxstats.NAMED:
            i, kind = i + 3 + struct.unpack(">H", raw[i + 1:i + 3])[0], kind - sqxstats.NAMED
        else:
            i += 2
        i += sqxstats.WIDTH[kind][2]
        out.append(raw[start:i])
    return b"".join(sorted(out))


def _canonical(node: ElementTree.Element, h: "hashlib._Hash") -> None:
    """Feed one element to `h` with its children in sorted order and its blobs as records.

    SQX writes a strategy's results as hash maps, so on each save the statistics blocks and
    the statistics inside each blob come out in another order (🔬 2026-09-29: «Parameters»
    and «DoFRatio» swapped, the per-sample blocks too; same length, no value changed) and
    settings.xml's CRC moves with nothing in it changed.
    """
    parts = []
    for child in node:
        sub = hashlib.blake2b(digest_size=16)
        _canonical(child, sub)
        parts.append(sub.digest())
    # A WFM result names its statistics by Java object address («SQStats@4f573d92»), new on every
    # save (🔬 2026-09-29: the WFM was re-exported at every stop for it): the class is kept.
    attrs = sorted((k, JAVA_REF.sub(r"\1", v)) for k, v in node.attrib.items())
    h.update(node.tag.encode() + repr(attrs).encode())
    text = (node.text or "").strip()
    h.update(_records(text) if node.tag == "SQStats" and node.get("e") == "b64" else text.encode())
    for part in sorted(parts):
        h.update(part)


@lru_cache(maxsize=8192)
def _entries(path: str, mtime_ns: int, size: int) -> str:
    """One .sqx's content: its zip entries' CRCs, settings.xml's read order-free (mtime and
    size are only the cache key)."""
    try:
        with zipfile.ZipFile(path) as z:
            parts = []
            for i in z.infolist():
                if i.filename == "settings.xml":
                    h = hashlib.blake2b(digest_size=16)
                    _canonical(ElementTree.fromstring(z.read(i)), h)
                    parts.append(f"settings:{h.hexdigest()}")
                else:
                    parts.append(f"{i.filename}:{i.CRC}:{i.file_size}")
            return "|".join(parts)
    except (OSError, zipfile.BadZipFile, ValueError, ElementTree.ParseError, struct.error):
        return f"unreadable:{mtime_ns}:{size}"       # half written: never equal to a sig


def fingerprint(sources: list[Path]) -> str:
    """What the strategies are, not when SQX last saved them.

    SQX rewrites every .sqx of every databank on its periodic sync, stamping each zip entry
    with the save time, so a file's date moved with nothing in it changed. The zip's own
    index carries each entry's CRC; settings.xml is read, its statistics in name order.
    """
    h = hashlib.blake2b(digest_size=16)
    for f in sorted(sources):
        st = f.stat()
        h.update(f"{f.name}={_entries(str(f), st.st_mtime_ns, st.st_size)}\n".encode())
    return h.hexdigest()


def age(done: Path | None, sources: list[Path]) -> str:
    """Whether an export is missing, older than the strategies it was made from, or fresh.

    Args:
        done: The export's marker (its manifest, or the folder that makes it complete).
        sources: The .sqx files it reads.

    Returns:
        `missing`, `stale` or `fresh`. A strategy added, curated away or retested after the
        export moves a file's time past the marker's; a time moved by SQX's resave alone
        does not: the export's `<marker>.sources.sig`, written the first time it is seen
        fresh, still matches `fingerprint`. Without that every worker stop re-exported every
        databank of the install (📓 2026-09-29: 8 min after a 20-min SPP run).
    """
    if done is None:
        return "missing"
    touched = max((f.stat().st_mtime for f in sources), default=0.0)
    folder = max((f.parent.stat().st_mtime for f in sources), default=0.0)   # a file removed
    sig = done.parent / f"{done.name}.sources.sig"
    if max(touched, folder) <= done.stat().st_mtime:
        now = fingerprint(sources)
        if not sig.exists() or sig.read_text() != now:
            sig.write_text(now)
        return "fresh"
    return "fresh" if sig.exists() and sig.read_text() == fingerprint(sources) else "stale"


def status(project: str, databank: str) -> dict:
    """Everything the window says about one databank's data, and why.

    Args:
        project: Project name.
        databank: Either spelling of the databank.

    Returns:
        `databank` as SQX spells it, `role`, `partner`, `strategies`, `writing`, and per
        piece its `state` (fresh | stale | missing | loading | none) and `what` it unlocks.
        `none` is a piece this databank does not have — a harvest needs a build databank.
    """
    db = find.spelled(project, databank)
    where = find.install_of(project, db)
    if where is None:
        return {"databank": db, "error": f"{project} / {db} no está en ninguna instalación"}
    role, top = where
    own = find.files(top, project, db)
    other = find.partner(top, project, db)
    theirs = find.files(top, project, other) if other else []
    metrics = metrics_export(project, db) / "manifest.json"
    states = {"metrics": age(metrics if metrics.exists() else None, own),
              "trades": age(newest(export_dir(project, db, "x").parent, "manifest.json"), own),
              "harvest": (age(newest(harvest_dir(project, db, "x").parent, "manifest.json"),
                              own + theirs) if other else "none")}
    why = {}
    # The newest loader job of each piece decides over the files: running is `loading`, and a
    # failure stays `failed` — never queued again on its own, or a conductor that refuses
    # would be asked every few seconds for ever — until the owner presses retry.
    last = {j["loader"]: j for j in jobs.listing()      # oldest first: the newest wins
            if j.get("loader") and j["project"] == project and j["databank"] == db}
    for piece, job in last.items():
        if job["rc"] is None:
            states[piece] = "loading"
        elif job["rc"] != 0 and not job["cancelled"]:
            states[piece] = "failed"
            why[piece] = " / ".join(job["tail"][-3:])
    return {"databank": db, "role": role, "partner": other, "strategies": len(own),
            "writing": find.writing(top, project),
            "pieces": {k: {"state": v, "what": PIECES[k], **({"why": why[k]} if k in why else {})}
                       for k, v in states.items()}}


def commands(project: str, now: dict) -> dict[str, tuple[str, list[str]]]:
    """The command that refreshes each missing or stale piece, with the lane it runs in.

    Args:
        project: Project name.
        now: What `status()` returned.

    Returns:
        Piece → (lane, argv after `python3`). Nothing when SQX is writing the project: its
        files are half-written, and the next selection after it finishes loads them.
    """
    if now.get("error") or now["writing"]:
        return {}
    db, role = now["databank"], now["role"]
    top = find.install_of(project, db)[1]
    at = [] if role == "master" else ["--role", role]
    want = {k for k, v in now["pieces"].items() if v["state"] in ("missing", "stale")}
    out = {}
    if "metrics" in want:
        out["metrics"] = ("python", ["-m", "sqx.export.export_metrics", "--project", project,
                                     "--databank", db, *at])
    first = find.files(top, project, db)[:1]
    if "trades" in want and first:
        out["trades"] = ("conductor", (
            ["-m", "sqx.export.export_retest", "--project", project, "--databank", db, *at]
            if find.cross_market(first[0]) else
            ["-m", "sqx.export.export_trades", "--project", project, "--databank", db,
             "--symbol", find.feed(first[0]), *at]))
    if "harvest" in want:
        out["harvest"] = ("conductor", ["-m", "studies.screening.gate.harvest", "--project",
                                        project, "--databank", db, "--oos-databank",
                                        now["partner"], *at])
    return out


def load(project: str, databank: str, retry: bool = False) -> dict:
    """Queue whatever this databank is missing, once, and say where it stands.

    Args:
        project: Project name.
        databank: Either spelling.
        retry: Queue the pieces whose last load failed as well.

    Returns:
        `status()` after queueing, with `queued`: the pieces this call started.
    """
    now = status(project, databank)
    if retry:
        now["pieces"] = {k: {**v, "state": "missing" if v["state"] == "failed" else v["state"]}
                         for k, v in now["pieces"].items()}
    todo = commands(project, now)
    for piece, (lane, argv) in todo.items():
        jobs.start(f"cargar {piece}", argv,
                   {"project": project, "databank": now["databank"], "strategy": "",
                    "study": f"cargar {piece}", "scope": "many", "loader": piece}, lane=lane)
    return {**status(project, databank), "queued": sorted(todo)}
