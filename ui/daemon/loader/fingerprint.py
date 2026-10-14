"""A databank's strategies reduced to one signature, so an export can tell a resave from a change."""

import base64
import hashlib
import re
import struct
import zipfile
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path
from xml.etree import ElementTree
from core import sqxfile, sqxstats
from core.fanout import CORES


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


def _canonical(node: ElementTree.Element, h: hashlib.blake2b) -> None:
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


def _entries(key: tuple[str, int, int]) -> str:
    """One .sqx's content (`key`: path, mtime_ns, size): its zip entries' CRCs, every XML entry
    read order-free — each result's `MonteCarloManipulation_Results.xml` holds hash-ordered
    SQStats too, and a bare stop moved all 571 fingerprints of a databank (🔬 2026-10-01)."""
    path, mtime_ns, size = key
    try:
        with zipfile.ZipFile(path) as z:
            parts = []
            for i in z.infolist():
                if i.filename.endswith(".xml"):
                    h = hashlib.blake2b(digest_size=16)
                    _canonical(ElementTree.fromstring(z.read(i)), h)
                    parts.append(f"{i.filename}:{h.hexdigest()}")
                else:
                    parts.append(f"{i.filename}:{sqxfile.mark(z, i)}:{i.file_size}")
            return "|".join(parts)
    except (OSError, zipfile.BadZipFile, ValueError, ElementTree.ParseError, struct.error):
        return f"unreadable:{mtime_ns}:{size}"       # half written: never equal to a sig


SEEN: dict[str, tuple[tuple[str, int, int], str]] = {}   # path → (key, content): one per file
POOL_FROM = 20                                           # fewer files than this: read here


def fingerprint(sources: list[Path]) -> str:
    """What the strategies are, not when SQX last saved them: its periodic sync rewrites every
    .sqx with the save time on each zip entry and nothing else changed.

    One file is ~19 ms, so 10,000 cost 3.2 min per call, several calls per stop
    (🔬 2026-10-04): the files not seen at their current date are read on every core.
    """
    files = sorted(sources)
    keys = [(str(f), st.st_mtime_ns, st.st_size) for f in files for st in [f.stat()]]
    cold = [k for k in keys if SEEN.get(k[0], (None,))[0] != k]
    if len(cold) >= POOL_FROM:
        with ProcessPoolExecutor(max_workers=min(CORES, len(cold)),
                                 mp_context=get_context("fork")) as pool:
            read = pool.map(_entries, cold, chunksize=max(1, min(50, len(cold) // CORES)))
            SEEN.update((k[0], (k, got)) for k, got in zip(cold, read))
    SEEN.update((k[0], (k, _entries(k))) for k in cold if SEEN.get(k[0], (None,))[0] != k)
    h = hashlib.blake2b(digest_size=16)
    for f, k in zip(files, keys):
        h.update(f"{f.name}={SEEN[k[0]][1]}\n".encode())
    return h.hexdigest()
