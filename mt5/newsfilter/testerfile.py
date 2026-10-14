"""Write a firm's restricted releases, in its server's clock, as the CSV the patched EA reads inside the Strategy Tester."""
import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from core.paths import MT5_DATA, MT5_PREFIX
from mt5.compare import OFFSET_ZONES
from mt5.newsfilter import forexfactory, history
from mt5.newsfilter.firms import FIRMS

KEPT = MT5_DATA / "calendar" / "tester"
COLUMNS = ["time", "tag", "source", "title"]
ALL_DAY = "Event takes all day"   # the terminal's words for CALENDAR_TIMEMODE_DATE


def name(firm: dict) -> str:
    """The file's name in Common\\Files — the EA's NewsTesterFile input carries the same."""
    return f"AlgoProjectNews_{firm['label']}.csv"


def common_files() -> Path:
    """The terminals' shared Common\\Files folder inside the prefix: the one place a tester agent reads from."""
    hits = list((MT5_PREFIX / "drive_c" / "users").glob("*/AppData/Roaming/MetaQuotes/Terminal/Common"))
    assert len(hits) == 1, f"expected one Common folder under {MT5_PREFIX}, found {len(hits)}"
    (hits[0] / "Files").mkdir(exist_ok=True)
    return hits[0] / "Files"


def to_server(utc: pd.Series, zone: str) -> pd.Series:
    """UTC instants as the naive clock of an MT5 server, with the hour change it had THAT day."""
    tz, hours = OFFSET_ZONES.get(zone, (zone, 0))
    return utc.dt.tz_localize("UTC").dt.tz_convert(tz).dt.tz_localize(None) + pd.Timedelta(hours=hours)


def releases(firm: dict, mt5: pd.DataFrame, ff: pd.DataFrame) -> pd.DataFrame:
    """What the live filter would have loaded over the whole history, one row per (minute, tag).

    Args:
        firm: One entry of firms.FIRMS.
        mt5: history.load().
        ff: forexfactory.load().

    Returns:
        time (server clock), tag (a currency, or OIL), source (MT5, FF or MT5+FF), title. An
        MT5 event with no minute — its type is all-day AND it is stamped 00:00 UTC, the
        placeholder — is left out, as the EA does live. Neither test alone will do: the RBA rate
        decision is filed as all-day with its real time, and a timed release can fall on 00:00.
    """
    parts = []
    if firm["mt5_calendar"]:
        mt5 = mt5[~((mt5["time_mode"] == ALL_DAY) & (mt5["utc"] == mt5["utc"].dt.normalize()))]  # pyright: ignore[reportAssignmentType]  # pandas/numpy stubs lose the type through indexing
        if firm["events"] is None:
            rows = mt5[mt5["importance"] == 3].assign(tag=lambda d: d["currency"])
        else:
            tag_of = {key: tag for tag, keys in firm["events"].items() for key in keys}
            rows = mt5.assign(tag=(mt5["country"] + ":" + mt5["code"]).map(tag_of)).dropna(subset=["tag"])
        parts.append(pd.DataFrame({"time": to_server(rows["utc"], firm["server_zone"]), "tag": rows["tag"],  # pyright: ignore[reportArgumentType]  # pandas/numpy stubs lose the type through indexing
                                   "source": "MT5", "title": rows["name"]}))
    if firm["forex_factory"]:
        red = ff[ff["impact"] == "High"]
        parts.append(pd.DataFrame({"time": to_server(red["utc"], firm["server_zone"]), "tag": red["currency"],  # pyright: ignore[reportArgumentType]  # pandas/numpy stubs lose the type through indexing
                                   "source": "FF", "title": red["event"]}))
    both = pd.concat(parts)
    return both.groupby(["time", "tag"], as_index=False).agg(  # pyright: ignore[reportReturnType]  # pandas/numpy stubs lose the type through indexing
        source=("source", lambda s: "+".join(sorted(set(s)))),
        title=("title", lambda s: " | ".join(dict.fromkeys(s))[:120]))


def text(rows: pd.DataFrame) -> str:
    """The CSV as MQL5 reads it: `YYYY.MM.DD HH:MM;tag;source;title`, ASCII, sorted by time, no header."""
    title = rows["title"].str.replace(";", ",").str.encode("ascii", "replace").str.decode("ascii")
    lines = rows["time"].dt.strftime("%Y.%m.%d %H:%M") + ";" + rows["tag"] + ";" + rows["source"] + ";" + title
    return "\r\n".join(lines) + "\r\n"


def read(path: Path) -> pd.DataFrame:
    """A tester CSV back as a frame: time, tag, source, title."""
    rows = pd.read_csv(path, sep=";", names=COLUMNS, dtype=str, keep_default_na=False)
    return rows.assign(time=pd.to_datetime(rows["time"], format="%Y.%m.%d %H:%M"))


def write(firm_key: str) -> dict[str, Any]:
    """Build the firm's file from the two histories in AlgoData; into Common\\Files, a copy kept in AlgoData."""
    firm = FIRMS[firm_key]
    rows = releases(firm, history.load(), forexfactory.load())
    target = common_files() / name(firm)
    KEPT.mkdir(parents=True, exist_ok=True)
    for path in (target, KEPT / name(firm)):
        path.write_bytes(text(rows).encode("ascii"))
    return {"file": str(target), "copy": str(KEPT / name(firm)), "rows": len(rows),
            "first": str(rows["time"].iloc[0]), "last": str(rows["time"].iloc[-1]),
            "by_source": rows["source"].value_counts().to_dict()}


def main() -> None:
    """CLI: python3 -m mt5.newsfilter.testerfile <firm>."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("firm", choices=sorted(FIRMS))
    key = ap.parse_args().firm
    got = write(key)
    print(f"{got['rows']} publicaciones restringidas de {FIRMS[key]['label']}, de {got['first']} a {got['last']} "
          f"(reloj del servidor, {FIRMS[key]['server_zone']})")
    print(f"  por fuente: {got['by_source']}")
    print(f"  -> {got['file']}\n  copia: {got['copy']}")


if __name__ == "__main__":
    main()
