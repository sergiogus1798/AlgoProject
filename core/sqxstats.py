"""Read a .sqx result without SQX: its stored metrics and its daily equity curve."""

import base64
import json
import re
import struct
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

IS, OOS, FULL = 10, 20, 127

# A record's type byte is 1 int / 2 long / 3 float, and the same plus 100 when the record
# carries its own name instead of an id. COLUMNS names the id-keyed ones; it was calibrated
# by matching a 107-column databank export of XAUUSD/WFM against the stored blobs, so a
# name suffixed "?" is one of a pair whose two members are equal on all 66 strategies.
NAMED = 100
WIDTH = {1: ("i", ">i", 4), 2: ("l", ">q", 8), 3: ("f", ">f", 4)}
COLUMNS = json.loads((Path(__file__).parent / "sqxstats_columns.json").read_text(encoding="utf-8"))

_BLOCK = re.compile(r'<stats_LQ1_direction_DD_(-?\d+)_L1_pl_DD_(\d+)_L1_sample_DD_(\d+)_L1__RQ1_'
                    r'[^>]*>\s*<SQStats version="\d+" e="b64">([^<]+)</SQStats>')


def records(blob: str) -> dict:
    """Decode one base64 SQStats blob into every statistic it holds.

    Args:
        blob: The text of an `<SQStats e="b64">` element.

    Returns:
        Metric name to value, 152 entries on this install. An id-keyed record whose id is
        not in COLUMNS -- it was zero on every strategy the calibration saw -- is reported
        as `stat:<f|i|l>:<id>`, the same key `core.optprofile` uses.
    """
    raw, out, i = base64.b64decode(blob), {}, 0
    while i < len(raw):
        kind = raw[i]
        if kind > NAMED:
            size = struct.unpack(">H", raw[i + 1:i + 3])[0]
            name, i, kind = raw[i + 3:i + 3 + size].decode(), i + 3 + size, kind - NAMED
        else:
            slot = f"{WIDTH[kind][0]}:{raw[i + 1]}"
            name, i = COLUMNS.get(slot, f"stat:{slot}"), i + 2
        _, fmt, width = WIDTH[kind]
        out[name] = struct.unpack(fmt, raw[i:i + width])[0]
        i += width
    return out


def stats(path: Path) -> dict:
    """Metrics SQX stored in a strategy's main result, per sample type.

    Args:
        path: A .sqx file.

    Returns:
        {sample type: {metric name: value}} for the Both/Money direction, keyed by the
        IS/OOS/FULL constants. These are the frozen values SQX shows in the databank --
        see knowhow/08-columns.md -- not a recomputation.
    """
    xml = zipfile.ZipFile(path).read("settings.xml").decode("utf8", errors="replace")
    return {int(sample): records(blob)
            for direction, pl, sample, blob in _BLOCK.findall(xml) if direction == "0"}


def equity(path: Path) -> pd.Series:
    """Daily cumulative P&L of a strategy's main result.

    Args:
        path: A .sqx file.

    Returns:
        Account-currency profit since the start of the backtest, indexed by date. The
        member is a Java-serialised stream: block markers 0x7a (4-byte length) and 0x77
        (1-byte), then a count followed by big-endian long-millis / double pairs.
    """
    archive = zipfile.ZipFile(path)
    member = next(n for n in archive.namelist() if n.endswith("dailyEquity.bin"))
    raw = archive.read(member)
    i, buf = 4, bytearray()
    while i < len(raw):
        marker = raw[i]
        if marker == 0x7A:
            size = struct.unpack(">i", raw[i + 1:i + 5])[0]
            buf += raw[i + 5:i + 5 + size]
            i += 5 + size
        elif marker == 0x77:
            size = raw[i + 1]
            buf += raw[i + 2:i + 2 + size]
            i += 2 + size
        else:
            break
    count = struct.unpack(">i", buf[:4])[0]
    pairs = np.frombuffer(buf[4:4 + 16 * count], dtype=np.dtype([("t", ">i8"), ("v", ">f8")]))
    return pd.Series(pairs["v"].astype("float64"),
                     index=pd.to_datetime(pairs["t"], unit="ms").normalize())
