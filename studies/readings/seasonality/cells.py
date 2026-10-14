"""Each oos1 trade placed on the calendar in UTC: its month, weekday and hour, at open and at close."""

import pandas as pd

# A zone the IANA database lacks, as SQX spells it: New York + 7 h
# (`knowhow/export/feed-clock-timezones.md`). Same table as mt5/compare.OFFSET_ZONES.
OFFSET_ZONES = {"EETUS": ("America/New_York", 7)}

ANCHORS = {"apertura": "Open time", "cierre": "Close time"}
DIMENSIONS = ("mes", "día", "hora")
MONTHS_ES = "ene feb mar abr may jun jul ago sep oct nov dic".split()
DAYS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def utc(times: pd.Series, zone: str) -> pd.Series:
    """Naive feed-clock times as naive UTC (owner, D-2: the calendar is read in UTC).

    Args:
        times: Naive, in `zone` — SQX stamps trades in its feed's broker clock.
        zone: IANA name, or a key of OFFSET_ZONES.

    Returns:
        Naive UTC; NaT where a change of hour repeats or skips the time (counted by the
        caller, never guessed).
    """
    name, hours = OFFSET_ZONES.get(zone, (zone, 0))
    local = (times - pd.Timedelta(hours=hours)).dt.tz_localize(
        name, ambiguous="NaT", nonexistent="NaT"
    )
    return local.dt.tz_convert("UTC").dt.tz_localize(None)


def cell_of(when: pd.Series, dimension: str) -> pd.Series:
    """The calendar cell a UTC time falls in: month 1-12, weekday 0-6 (Monday 0), hour 0-23."""
    if dimension == "mes":
        return when.dt.month
    if dimension == "día":
        return when.dt.dayofweek
    return when.dt.hour


def label(dimension: str, cell: int) -> str:
    """A cell's name as the reader sees it, e.g. «mar», «martes», «14h UTC»."""
    if dimension == "mes":
        return MONTHS_ES[cell - 1]
    if dimension == "día":
        return DAYS_ES[cell]
    return f"{cell:02d}h UTC"


def place(trades: pd.DataFrame, zone: str) -> pd.DataFrame:
    """One strategy's oos1 trades on the UTC calendar.

    Args:
        trades: One strategy's oos1 rows of a harvest's trades.parquet (`Open time`,
            `Close time`, `Profit/Loss` in account currency, `Size` in lots).
        zone: The feed's clock (`sqx.inspect.feeds.timezone`).

    Returns:
        One row per trade whose two times exist in UTC: `pnl` (account currency), `per_lot`
        (pnl / Size — the unit the null shuffles, so position sizing that grows with equity
        does not read as a season), `stratum` (the open's UTC year-month as an integer: the
        null shuffles only inside it), and per anchor `<dimension>·<anchor>` cells plus
        `block·<anchor>` (that anchor's year-month, the unit the month null relabels).
        `attrs["dropped"]` counts the trades lost to a change of hour.
    """
    if (trades["Size"] <= 0).any():
        raise ValueError(
            "seasonality: a trade with Size <= 0 in the harvest; re-harvest it"
        )
    out = pd.DataFrame(
        {
            "pnl": trades["Profit/Loss"].to_numpy(),
            "per_lot": (trades["Profit/Loss"] / trades["Size"]).to_numpy(),
        }
    )
    for anchor, column in ANCHORS.items():
        when = utc(pd.to_datetime(trades[column]), zone).reset_index(drop=True)
        out[f"_t·{anchor}"] = when
        out[f"block·{anchor}"] = when.dt.year * 12 + when.dt.month - 1
        for dimension in DIMENSIONS:
            out[f"{dimension}·{anchor}"] = cell_of(when, dimension)
    kept = out.dropna().reset_index(drop=True)
    kept["stratum"] = kept["block·apertura"]
    kept = kept.drop(columns=[f"_t·{a}" for a in ANCHORS]).astype(
        {c: "int64" for c in out.columns if "·" in c and not c.startswith("_")}
    )
    kept.attrs["dropped"] = len(out) - len(kept)
    return kept
