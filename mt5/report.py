"""Read a Strategy Tester HTML report: its summary figures, its deals, and the trades they make."""

import re
from typing import Any
from pathlib import Path

import pandas as pd
from lxml import html

# The Deals table, in the order MT5 writes it. Rows are found by shape (13 cells, a timestamp
# first), not by the section title, which comes in the terminal's language.
DEAL_COLUMNS = [
    "Time",
    "Deal",
    "Symbol",
    "Type",
    "Direction",
    "Volume",
    "Price",
    "Order",
    "Commission",
    "Swap",
    "Profit",
    "Balance",
    "Comment",
]
STAMP = re.compile(r"^\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}(:\d{2})?$")
NUMERIC = ["Volume", "Price", "Commission", "Swap", "Profit", "Balance"]


def _number(text: str) -> float:
    """MT5 writes thousands with spaces: '10 000.00'."""
    return float(text.replace(" ", "").replace("\xa0", "")) if text.strip() else 0.0


def read(path: Path) -> tuple[dict, pd.DataFrame]:
    """Parse one report.

    Args:
        path: The .htm the tester wrote (UTF-16).

    Returns:
        (summary as {label: text} for every "label:" cell followed by a value, deals frame
        with DEAL_COLUMNS, numbers as floats, Time as datetime in the server's clock).
    """
    raw = path.read_bytes()
    tree = html.fromstring(
        raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw
    )
    summary, deals = {}, []
    for row in tree.iter("tr"):
        cells = [c.text_content().strip() for c in row if c.tag in ("td", "th")]
        if len(cells) == len(DEAL_COLUMNS) and STAMP.match(cells[0]):
            deals.append(cells)
            continue
        for label, value in zip(cells, cells[1:]):
            if label.endswith(":") and value and not value.endswith(":"):
                summary.setdefault(label[:-1], value)
    frame = pd.DataFrame(deals, columns=pd.Index(DEAL_COLUMNS))
    frame["Time"] = pd.to_datetime(frame["Time"], format="mixed")
    for col in NUMERIC:
        frame[col] = frame[col].map(_number)
    return summary, frame


def trades(deals: pd.DataFrame) -> pd.DataFrame:
    """Pair entry and exit deals into trades, in SQX's trade-export shape.

    One position at a time per symbol, as SQX's EAs trade; an exit in parts closes the trade
    when its volume is spent, at the volume-weighted price. P/L carries commission and swap.

    Returns:
        Type (Buy/Sell), Open time, Open price, Size, Close time, Close price, Profit/Loss.
    """
    if (deals["Direction"] == "in/out").any():
        raise SystemExit(
            "the report has in/out (reversal) deals: pairing them is not built"
        )
    rows, open_ = [], {}
    d: Any
    for d in deals[deals["Direction"].isin(["in", "out"])].itertuples(index=False):
        if d.Direction == "in":
            if d.Symbol in open_:
                raise SystemExit(
                    f"{d.Time}: a second position on {d.Symbol} while one is open"
                )
            open_[d.Symbol] = {
                "Type": d.Type.capitalize(),
                "Open time": d.Time,
                "Open price": d.Price,
                "Size": d.Volume,
                "left": d.Volume,
                "value": 0.0,
                "pl": d.Commission + d.Swap,
            }
            continue
        t = open_[d.Symbol]
        t["left"] -= d.Volume
        t["value"] += d.Price * d.Volume
        t["pl"] += d.Profit + d.Commission + d.Swap
        if t["left"] <= 1e-9:
            rows.append(
                {
                    "Type": t["Type"],
                    "Open time": t["Open time"],
                    "Open price": t["Open price"],
                    "Size": t["Size"],
                    "Close time": d.Time,
                    "Close price": t["value"] / t["Size"],
                    "Profit/Loss": round(t["pl"], 2),
                }
            )
            del open_[d.Symbol]
    return pd.DataFrame(
        rows,
        columns=pd.Index(
            [
                "Type",
                "Open time",
                "Open price",
                "Size",
                "Close time",
                "Close price",
                "Profit/Loss",
            ]
        ),
    )


def start_check(
    summary: dict, trades: pd.DataFrame, log: str, expert: str, asked: str
) -> dict[str, Any]:
    """What the tester really covered, beside what was asked. No floor: the quality is reported only.

    Args:
        summary: `read`'s summary (its `History Quality` cell, e.g. "22%").
        trades: `trades()` of the same report.
        log: The tester journal of the run's day, decoded.
        expert: The run's `Expert=` (as in run.json), to find its pass in the journal.
        asked: The start date asked, YYYY-MM-DD.

    Returns:
        {"history_quality_pct": float | None, "first_trade": "YYYY-MM-DD" | None,
        "start_asked", "start_actual": the date of the journal's «start time changed to» line, or
        `asked` when there is none, "start_changed": bool}. The journal names the date the
        tester moved the start to; the first trade only says when the EA first traded.
    """
    quality = summary.get("History Quality", "").rstrip("%")
    actual = asked
    lines = log.splitlines()
    mine = [i for i, l in enumerate(lines) if "\tTester\t" in l and expert in l]
    for l in lines[mine[-1] + 1 :] if mine else []:
        if "\tTester\t" in l and "testing of" in l:
            break
        found = re.search(r"start time changed to (\d{4})\.(\d\d)\.(\d\d)", l)
        if found:
            actual = "-".join(found.groups())
            break
    return {
        # 🔬 open_prices reports «n/a» (the months probe, 2026-10-17)
        "history_quality_pct": float(quality) if quality and quality != "n/a" else None,
        "first_trade": str(trades["Open time"].min().date()) if len(trades) else None,
        "start_asked": asked,
        "start_actual": actual,
        "start_changed": actual != asked,
    }
