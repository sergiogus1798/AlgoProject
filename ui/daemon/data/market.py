"""One asset's data as the Datos zone shows it: its feeds, its bars, and its step-4 studies off the disk."""

import json

from core import barstore
from core.datapaths import spread_dir
from core.paths import feed_quality_dir

TIMEFRAMES = ("D1", "H4", "H1")      # what the zone draws; M1 is 8 M rows and M30 adds nothing here
# Each step-4 report is a contract dict the study already wrote beside its tables; the
# window reads it back, never recomputes it. part → (folder of one feed, file, command).
STUDIES = {
    "spread": (spread_dir, "spread.json", "python3 -m studies.data.spread.scan --symbol {s}"),
    "band": (spread_dir, "band.json", "python3 -m studies.data.spread.bands --symbol {s}"),
    "feedQuality": (feed_quality_dir, "feedQuality.json",
                    "python3 -m studies.data.feedQuality.scan --feed {f}"),
}


def feeds(folder: str) -> list[str]:
    """The feed folders a study has written, sorted.

    Args:
        folder: "spread" or "feedQuality".

    Returns:
        Folder names; the library-wide files beside them (calendar, calibration) are not feeds.
        Empty when the study never ran on this machine: the zone then says so per asset.
    """
    top = spread_dir() if folder == "spread" else feed_quality_dir()
    if not top.is_dir():         # the window's boundary: a fresh data root has neither tree
        return []
    return sorted(p.name for p in top.iterdir() if p.is_dir())


def assets() -> list[dict]:
    """Every asset any of the three data trees knows, with the feed each one uses for it.

    Returns:
        One dict per symbol (the feed name up to its first underscore), sorted: `symbol`,
        `bars`, `spread` and `feedQuality` — the feed name or None — and, when the bar
        library has it, `from`, `to` and `count` of its M1 bars.
    """
    library = barstore.library()
    out: dict[str, dict] = {}
    for kind, names in (("bars", sorted(library)), ("spread", feeds("spread")),
                        ("feedQuality", feeds("feedQuality"))):
        for feed in names:
            row = out.setdefault(feed.split("_")[0], {"bars": None, "spread": None,
                                                      "feedQuality": None})
            row[kind] = row[kind] or feed     # two feeds of one symbol: the first, sorted
    for row in out.values():
        if row["bars"]:
            lib = library[row["bars"]]
            row.update({"from": lib["from"], "to": lib["to"], "count": lib["bars"]})
    return [{"symbol": s, **out[s]} for s in sorted(out)]


def bars(feed: str, tf: str, since: str) -> dict:
    """One feed's OHLC at one timeframe, columnar.

    Args:
        feed: A feed of the bar library.
        tf: One of TIMEFRAMES.
        since: First day kept as YYYY-MM-DD, empty for the whole history.

    Returns:
        `{feed, tf, rows, t, o, h, l, c}`, t as "YYYY-MM-DD HH:MM". Resampled from M1 by
        `core.barstore`, which caches it in `barsDerived/` under the M1's fingerprint; the
        first call of a timeframe pays the resample (~1 s), the next ones read the cache.
    """
    frame = barstore.read(feed, tf)
    if since:
        frame = frame[frame.index >= since]
    return {"feed": feed, "tf": tf, "rows": len(frame),
            "t": frame.index.strftime("%Y-%m-%d %H:%M").tolist(),
            "o": frame["Open"].tolist(), "h": frame["High"].tolist(),
            "l": frame["Low"].tolist(), "c": frame["Close"].tolist()}


def study(part: str, feed: str) -> dict:
    """One feed's step-4 report as its study wrote it.

    Args:
        part: A key of STUDIES.
        feed: The feed folder the study wrote under.

    Returns:
        `{"result": contract dict}`, or `{"error": sentence}` naming the command that writes
        it when the feed was never scanned.
    """
    folder, name, command = STUDIES[part]
    path = folder(feed) / name
    if not path.exists():
        return {"error": f"{feed} no tiene {name} todavía. Lo escribe: "
                         + command.format(s=feed.split("_")[0], f=feed)}
    return {"result": json.loads(path.read_text(encoding="utf-8"))}
