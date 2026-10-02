"""Export the MT5 terminal's economic calendar to AlgoData in UTC: every event type and every dated release."""
import argparse
import datetime as dt

import pandas as pd

from core.paths import MT5_DATA
from mt5.newsfilter import terminal

CAL = MT5_DATA / "calendar"
EVENTS = CAL / "mt5_events.parquet"
VALUES = CAL / "mt5_values.parquet"
IMPORTANCE = {"Importance is not set": 0, "Low importance": 1, "Medium importance": 2,
              "High importance": 3}
FIRST_YEAR = 2000   # the terminal answered nothing before 2007 (2026-10-02); asked from here anyway


def server_shift(s: dict) -> pd.Timedelta:
    """Server clock minus UTC right now, to the quarter hour.

    The calendar stamps EVERY release, past ones included, at UTC plus today's offset — not the
    offset the server had that day (knowhow/eng/mt5-calendar-history-clock.md). Subtracting
    today's offset therefore gives UTC for the whole history, in summer and in winter.
    """
    now = terminal.call(s, "get_time_information", {})
    gap = pd.Timestamp(now["trade_server_last_known_time"]) - pd.Timestamp(now["utc_time"]).tz_localize(None)
    return gap.round("15min")


def events(s: dict) -> pd.DataFrame:
    """The catalogue: one row per event type, with its country, currency, code and importance."""
    rows = []
    for c in terminal.call(s, "economic_calendar_list_countries", {})["countries"]:
        got = terminal.call(s, "economic_calendar_list_events_by_country", {"country_code": c["country_code"]})
        rows += [{"event_id": int(e["id"]), "country": c["country_code"], "currency": c["currency"],
                  "code": e["event_code"], "name": e["name"], "importance": IMPORTANCE[e["importance"]],
                  "type": e["type"], "time_mode": e["time_mode"]} for e in got["events"]]
    return pd.DataFrame(rows)


def values(s: dict, first_year: int) -> pd.DataFrame:
    """Every dated release from `first_year` to the end of next year.

    `utc` is the release; `stamp` is what the terminal showed the day of the export (UTC plus
    that day's offset) — kept for the all-day events, which sit at 00:00 of the stamp's day.
    """
    shift = server_shift(s)
    rows = []
    for year in range(first_year, dt.date.today().year + 2):
        got = terminal.call(s, "economic_calendar_list_values", {
            "datetime_from": f"{year}-01-01T00:00:00", "datetime_to": f"{year + 1}-01-01T00:00:00",
            "limit": 1000000})
        assert not got["truncated"], f"{year}: the terminal cut the answer"
        rows += [{"value_id": int(v["id"]), "event_id": int(v["event_id"]),
                  "utc": pd.Timestamp(v["time"]) - shift, "stamp": pd.Timestamp(v["time"]),
                  "actual": v["actual_value"], "forecast": v["forecast_value"],
                  "previous": v["prev_value"]} for v in got["values"]]
    return pd.DataFrame(rows).drop_duplicates("value_id").sort_values("utc", ignore_index=True)


def export(first_year: int = FIRST_YEAR) -> dict:
    """Write both tables under MT5_DATA/calendar and say what span the terminal gave.

    Importance is the event type's rating TODAY: the calendar keeps no history of it.
    """
    CAL.mkdir(parents=True, exist_ok=True)
    s = terminal.session()
    ev, va = events(s), values(s, first_year)
    ev.to_parquet(EVENTS)
    va.to_parquet(VALUES)
    return {"events": len(ev), "high": int((ev["importance"] == 3).sum()), "values": len(va),
            "first": str(va["utc"].iloc[0]), "last": str(va["utc"].iloc[-1]),
            "shift_h": server_shift(s) / pd.Timedelta(hours=1)}


def load() -> pd.DataFrame:
    """Every release joined to its event type: utc, country, currency, code, name, importance."""
    return pd.read_parquet(VALUES).merge(pd.read_parquet(EVENTS), on="event_id")


def main() -> None:
    """CLI: python3 -m mt5.newsfilter.history [--from YEAR] — the terminal must be open."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from", dest="first", type=int, default=FIRST_YEAR,
                    help="primer año que se pide; por defecto todo lo que el terminal tenga")
    got = export(ap.parse_args().first)
    print(f"calendario de MT5 -> {CAL}")
    print(f"  {got['events']} tipos de evento ({got['high']} de importancia alta), {got['values']} publicaciones")
    print(f"  de {got['first']} a {got['last']} UTC  (reloj del servidor hoy: UTC{got['shift_h']:+g} h)")


if __name__ == "__main__":
    main()
