"""The live side: an account's deals of one week as trades in the project's trade frame, per strategy."""
import pandas as pd

from mt5 import live as terminal
from mt5.reconcile import week as weeks

# MetaTrader5's own codes, as `history_deals_get` returns them (DEAL_TYPE_*, DEAL_ENTRY_*).
BUY, SELL = 0, 1
IN, OUT, INOUT, OUT_BY = 0, 1, 2, 3
COLUMNS = ["magic", "symbol", "position", "Type", "Open time", "Open price", "Size",
           "Close time", "Close price", "Profit/Loss", "Commission", "Swap"]


def fetch(account: dict, week: str, spill_days: int) -> list[dict]:
    """The account's deals from the week's Monday to `spill_days` past its end. READ-ONLY.

    Args:
        account: `{login, server}` of `core.paths.MT5_ACCOUNTS`; the terminal logs into it
            with the password it has saved (the investor one is enough: nothing is sent).
        week: "YYYY-Www".
        spill_days: Days past the week's end, for the exits of trades opened inside it.

    Returns:
        `history_deals_get` rows as dicts (`winside/query.py`'s `history` verb). ⚠️ This
        switches the open terminal to that account, as every `mt5.live.ask(account=…)` does.
    """
    start, end = weeks.bounds(week)
    end += pd.Timedelta(days=spill_days)
    got = terminal.ask("history", {"start": f"{start:%Y-%m-%d %H:%M}",
                                   "end": f"{end:%Y-%m-%d %H:%M}"}, account)
    if isinstance(got, dict) and got.get("error"):
        raise SystemExit(f"el terminal no dio el historial de {account['server']}: {got['error']}")
    return got


def trades(deals: list[dict]) -> pd.DataFrame:
    """Deals grouped by position into trades, in schema T as far as MT5 gives it.

    A position is its entry deals and its exit deals (`position_id`): open price and close
    price volume-weighted, `Profit/Loss` net (profit + commission + swap + fee of every deal
    of the position, as T's net), times naive on the server's clock, the magic number of the
    ENTRY deal (a stop the server fills carries none). Balance and credit deals are not trades.
    A position not fully closed in the deals read keeps `Close time` NaT. MT5 gives no
    MAE/MFE: `floating.py` rebuilds them from M1.

    Args:
        deals: `history_deals_get` rows as dicts: ticket, time (s), type, entry, magic,
            position_id, volume, price, commission, swap, profit, fee, symbol.

    Returns:
        COLUMNS, one row per position, by open time.
    """
    d = pd.DataFrame(deals)
    if d.empty:
        return pd.DataFrame(columns=COLUMNS)
    d = d[d["type"].isin([BUY, SELL])]
    if d["entry"].isin([INOUT, OUT_BY]).any():
        raise SystemExit("el historial tiene deals de reversión o de cierre por contraria "
                         "(in/out, out by): emparejarlos no está construido")
    rows = []
    for position, g in d.sort_values("time").groupby("position_id", sort=False):
        ins, outs = g[g["entry"] == IN], g[g["entry"] == OUT]
        if ins.empty:                       # opened before the stretch read: not this week's
            continue
        size = float(ins["volume"].sum())
        closed = len(outs) and abs(float(outs["volume"].sum()) - size) < 1e-9
        rows.append({
            "magic": int(ins["magic"].iloc[0]), "symbol": ins["symbol"].iloc[0],
            "position": int(position), "Type": "Buy" if ins["type"].iloc[0] == BUY else "Sell",
            "Open time": pd.to_datetime(int(ins["time"].iloc[0]), unit="s"),
            "Open price": float((ins["price"] * ins["volume"]).sum() / size), "Size": size,
            "Close time": pd.to_datetime(int(outs["time"].iloc[-1]), unit="s") if closed
            else pd.NaT,
            "Close price": float((outs["price"] * outs["volume"]).sum() / size) if closed
            else float("nan"),
            "Profit/Loss": round(float(g[["profit", "commission", "swap", "fee"]].sum().sum()), 2),
            "Commission": float(g["commission"].sum() + g["fee"].sum()),
            "Swap": float(g["swap"].sum())})
    out = pd.DataFrame(rows, columns=COLUMNS)
    return out.astype({"Open time": "datetime64[ns]", "Close time": "datetime64[ns]"}
                      ).sort_values("Open time").reset_index(drop=True)


def by_strategy(frame: pd.DataFrame, firm: str, register: pd.DataFrame
                ) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Split one account's trades by magic number into the register's strategies.

    Args:
        frame: `trades()` of one account.
        firm: That account's key.
        register: `register.read()`.

    Returns:
        ({strategy: its trades}, the trades whose magic the register does not name for this
        firm — a hand-placed order has magic 0 — reported, never dropped in silence). Every
        registered strategy of the firm has a frame, empty when it did not trade.
    """
    mine = register[register["firm"] == firm]
    known = {int(r.magic): r.strategy for r in mine.itertuples()}
    split = {name: frame[frame["magic"] == magic].reset_index(drop=True)
             for magic, name in known.items()}
    return split, frame[~frame["magic"].isin(list(known))].reset_index(drop=True)
