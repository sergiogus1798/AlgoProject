"""Which trading session each entry falls in: the feed's clock to UTC, then each city's own hours.

The day is cut by where the three cities' working hours overlap, each in its own local time so
daylight saving moves every boundary on its own date (owner, 2026-09-26):

    Tokio 09-18 · Londres 08-17 · Nueva York 08-17, local time
    Tokio and Londres both open  -> "Solape Asia-Londres"
    Londres and Nueva York open  -> "Solape Londres-NY"
    only one open                -> "Asia", "Londres", "Nueva York"
    none open                    -> "Fuera de sesión"

Tokio and Nueva York never overlap, so the six labels partition the day.
"""

import numpy as np
import pandas as pd

ORDER = ("Asia", "Solape Asia-Londres", "Londres", "Solape Londres-NY", "Nueva York",
         "Fuera de sesión")

# SQX's own zone for some brokers: EET offsets on the US daylight-saving calendar, which is
# New York's clock plus seven hours. It has no IANA name, so zoneinfo cannot read it.
US_EET_SHIFT = pd.Timedelta(hours=7)


def to_utc(times: pd.Series, zone: str) -> pd.DatetimeIndex:
    """Naive feed-clock timestamps as UTC instants.

    Args:
        times: Entry times as the trade export writes them — naive, in the feed's clock.
        zone: `sqx.inspect.feeds.timezone(feed)`.

    Returns:
        The same instants in UTC. An hour the clock repeats or skips at a change of time is
        NaT, and is left out of every session rather than guessed.
    """
    stamps = pd.DatetimeIndex(times)
    if zone == "EETUS":
        stamps, zone = stamps - US_EET_SHIFT, "America/New_York"
    local = stamps.tz_localize(zone, ambiguous="NaT", nonexistent="NaT")
    return local.tz_convert("UTC")


def label(utc: pd.DatetimeIndex, cities: dict) -> np.ndarray:
    """Each instant's session name.

    Args:
        utc: Entry instants in UTC (`to_utc`).
        cities: The `sessions` block of config.yaml — per city its IANA zone and its opening
            and closing hour, local.

    Returns:
        One label from ORDER per instant, or "" where the instant is NaT.
    """
    open_ = {}
    for city, spec in cities.items():
        hour = utc.tz_convert(spec["zone"]).hour
        open_[city] = (hour >= spec["open"]) & (hour < spec["close"])
    asia, london, ny = open_["asia"], open_["london"], open_["new_york"]
    out = np.select([london & ny, asia & london, asia, london, ny],
                    ["Solape Londres-NY", "Solape Asia-Londres", "Asia", "Londres",
                     "Nueva York"], default="Fuera de sesión")
    return np.where(utc.isna(), "", out)
