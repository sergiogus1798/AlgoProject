"""Forex Factory's calendar history from 2007 (janickfarrell/newfac's daily release, MIT), as UTC rows."""
import argparse
import urllib.request

import pandas as pd

from mt5.newsfilter.history import CAL

# Scraped with Forex Factory's own GMT cookie, republished every night at 00:10 UTC.
URL = "https://github.com/janickfarrell/newfac/releases/download/calendar-data/forexfactory_calendar.csv"
RAW = CAL / "ff_newfac.csv"
# A second scrape of the red folder only, 2020 on, stamped in UTC (ehsanrs2/forexfactory-scraper:
# GPL code, never run or copied — only its published CSV is read, to check the first one's clock).
CHECK = CAL / "ff_ehsanrs2_high.csv"


def download() -> int:
    """Fetch the day's CSV over the previous one; returns its size in bytes."""
    CAL.mkdir(parents=True, exist_ok=True)
    data = urllib.request.urlopen(URL, timeout=300).read()
    RAW.write_bytes(data)
    return len(data)


def load() -> pd.DataFrame:
    """Every row with a clock time: utc, currency, impact (High/Medium/Low), event.

    Rows whose time is not HH:MM ("All Day", "Tentative", "Day 2"…) have no minute to block
    around and are left out; `untimed()` counts them.
    """
    raw = pd.read_csv(RAW, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    timed = raw[raw["time"].str.fullmatch(r"\d{1,2}:\d{2}")]
    utc = pd.to_datetime(timed["date"].str.split(" ", n=1).str[1] + " " + timed["time"],
                         format="%b %d %Y %H:%M")
    return pd.DataFrame({"utc": utc, "currency": timed["currency"], "impact": timed["impact"],
                         "event": timed["event"]}).sort_values("utc", ignore_index=True)


def untimed() -> pd.Series:
    """How many red-folder rows carry no clock time, by what they say instead."""
    raw = pd.read_csv(RAW, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    red = raw[raw["impact"] == "High"]
    return red.loc[~red["time"].str.fullmatch(r"\d{1,2}:\d{2}"), "time"].value_counts()


def load_check() -> pd.DataFrame:
    """The second scrape's red folder: utc, currency, event."""
    raw = pd.read_csv(CHECK)
    utc = pd.to_datetime(raw["DateTime"], utc=True).dt.tz_localize(None)
    return pd.DataFrame({"utc": utc, "currency": raw["Currency"], "event": raw["Event"]})


def main() -> None:
    """CLI: python3 -m mt5.newsfilter.forexfactory — downloads today's file and says its span."""
    argparse.ArgumentParser(description=__doc__).parse_args()
    size = download()
    rows = load()
    red = rows[rows["impact"] == "High"]
    print(f"Forex Factory -> {RAW}  ({size / 1e6:.1f} MB)")
    print(f"  {len(rows)} filas con hora, de {rows['utc'].iloc[0]} a {rows['utc'].iloc[-1]} UTC")
    print(f"  carpeta roja: {len(red)} con hora, {int(untimed().sum())} sin hora (no entran en el filtro)")


if __name__ == "__main__":
    main()
