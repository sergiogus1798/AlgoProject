"""Naive feed-clock times to UTC, and the day a UTC instant belongs to in any server clock."""

import pandas as pd

# SQX's EETUS and the NY-close MT5 server convention have no IANA name: New York + 7 h
# (knowhow/export/feed-clock-timezones.md).
NY_PLUS_7 = "EETUS"
NEW_YORK = "America/New_York"
SHIFT = pd.Timedelta(hours=7)


def to_utc(times: pd.DatetimeIndex, zone: str) -> tuple[pd.DatetimeIndex, int]:
    """Localise naive clock times and convert them to UTC.

    Args:
        times: Naive timestamps as SQX stamps bars and trades.
        zone: An IANA name, or "EETUS" for New York + 7 h.

    Returns:
        The UTC instants, and how many were NaT: the hour a change of time repeats or skips
        is never guessed, it is dropped and counted.
    """
    if zone == NY_PLUS_7:
        local = (times - SHIFT).tz_localize(NEW_YORK, ambiguous="NaT", nonexistent="NaT")
    else:
        local = times.tz_localize(zone, ambiguous="NaT", nonexistent="NaT")
    utc = local.tz_convert("UTC")
    return utc, int(utc.isna().sum() - times.isna().sum())


def local(utc: pd.DatetimeIndex, zone: str) -> pd.DatetimeIndex:
    """UTC instants read on a server's wall clock, naive."""
    if zone == NY_PLUS_7:
        return utc.tz_convert(NEW_YORK).tz_localize(None) + SHIFT
    return utc.tz_convert(zone).tz_localize(None)


def day_of(utc: pd.DatetimeIndex, zone: str) -> pd.DatetimeIndex:
    """The server day each instant falls in: naive midnight of the zone's own calendar date."""
    return local(utc, zone).normalize()


def day_end(days: pd.DatetimeIndex, zone: str) -> pd.DatetimeIndex:
    """The UTC instant each server day ends — the next midnight on that server's clock.

    Args:
        days: Naive day labels as day_of() returns them.
        zone: As for to_utc().

    Returns:
        UTC instants. A midnight never falls in a repeated or skipped hour in these zones,
        so none is NaT.
    """
    return to_utc(days + pd.Timedelta(days=1), zone)[0]
