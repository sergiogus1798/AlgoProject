"""A prop firm's conditions for one symbol, read off its own MT5 account and put in SQX's units."""

from typing import Any

import pandas as pd

from mt5 import guard, live

# MT5's ENUM_SYMBOL_SWAP_MODE → SQX's <Swap type>. The ones left out (swap in the base or the
# margin currency, reopen modes) have no SQX equivalent: a firm quoting one is refused.
SWAP_TYPES = {0: None, 1: "points", 4: "money", 5: "percent", 6: "percent"}
# MT5 numbers the triple-swap day from Sunday = 0; SQX spells it.
DAYS = ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"]


class Refused(Exception):
    """This firm cannot be priced for this symbol; the message says why, in Spanish."""


def read(symbol: str, account: dict) -> dict[str, Any]:
    """The symbol's specification as the firm's server gives it right now.

    Args:
        symbol: The firm's name for it, e.g. XAUUSD.h.
        account: `{login, server}`: the terminal logs into it with its saved password.

    Returns:
        MT5's symbol_info as a dict (spread in points, point, digits, swap_*, …), plus the
        account's `account_leverage` and `account_currency` — the tester is given the same —
        and `first_bar`, the day of the server's first monthly bar (None when it gives none):
        how far back «Desde = MT5» can reach.
        Refused when the terminal is not on that account afterwards.
    """
    guard.refuse(account)
    info = live.ask("symbol", {"symbol": symbol}, account)
    if not isinstance(info, dict) or "error" in info or info.get("point") is None:
        raise Refused(f"MT5 no da {symbol} en {account['server']}: {info}")
    held = live.ask("account", {}, account)
    if not isinstance(held, dict) or held.get("login") != account["login"]:
        raise Refused(
            f"el terminal no entró en la cuenta {account['login']} de "
            f"{account['server']}: {held}"
        )
    first = live.ask("first", {"symbol": symbol}, account)
    return {
        **info,
        "account_leverage": held["leverage"],
        "account_currency": held["currency"],
        "first_bar": first.get("first") if isinstance(first, dict) else None,
    }


GAP_SHARE = (
    0.5  # a month with under this share of the firm's median month of H1 bars is a hole
)


def holes(times: pd.Series, window: tuple[str, str]) -> list[str]:
    """The whole months of the window where the firm's server has too few bars to trade.

    Args:
        times: The H1 bar times the server gave for the window.
        window: (first day, last day), YYYY-MM-DD.

    Returns:
        «YYYY-MM» of each whole month inside the window with fewer H1 bars than `GAP_SHARE` of
        the median whole month. The yardstick is the firm's own median, not SQX's feed: no
        second data path, and one hole in 24 months never moves a median (🔬 Hantec
        USDJPY/GBPJPY: 2022-06 and 2023-01 with no bars; December still holds ~85 % of it).
        The window's partial first and last months are never judged.
    """
    first, last = (pd.Timestamp(d) for d in window)
    months = pd.period_range(first, last, freq="M")
    months = [
        m for m in months if m.start_time >= first and m.end_time.normalize() <= last
    ]
    if not months:
        return []
    per = (
        pd.Series(1, index=pd.to_datetime(times).dt.to_period("M"))
        .groupby(level=0)
        .sum()
    )
    per = per.reindex(months, fill_value=0)
    return [str(m) for m, n in per.items() if n < GAP_SHARE * per.median()]


def gap_months(symbol: str, account: dict, window: tuple[str, str]) -> list[str]:
    """`holes` of the H1 bars the firm's server gives for the window (one query)."""
    got = live.series("bars", symbol, window[0], window[1], "H1", account)
    if not got["rows"]:
        return []
    return holes(pd.Series(pd.read_parquet(got["file"])["time"]), window)


def for_sqx(
    data: dict, firm: str, info: dict, slippage: float
) -> tuple[dict, list[str]]:
    """The firm's costs in `core.assetdata.sqx_settings`' shape, for `setups.write_setup`.

    Args:
        data: The asset as `core.assetdata.load` returns it — its SQX tick size, its
            commission per broker, the swap's rollover hour.
        firm: The firm's key, e.g. "ftmo".
        info: `read()`'s answer.
        slippage: SQX's slippage in points, from config.yaml.

    Returns:
        The settings and one Spanish line per figure, saying where it came from. The spread
        is the one the firm quotes at the moment of reading (owner, 2026-09-29: «spread actual
        del símbolo»), turned from the firm's points into SQX's.

    Raises:
        Refused: The commission for this firm is not confirmed in `assets/`, or the swap is
            quoted in a mode SQX cannot express. Never guessed (hard rule 5).
    """
    tick = data["instrument"]["tick_size"]
    spread = round(info["spread"] * info["point"] / tick, 4)
    brokers = data["costs"]["commission"].get("brokers") or {}
    com = brokers.get(firm) or {}
    if com.get("method") is None or com.get("value") is None:
        raise Refused(
            f"{data['symbol']} no tiene comisión confirmada de {firm} en "
            f"assets/symbols/{data['symbol']}.yaml (costs.commission.brokers.{firm}): "
            "complétala en la zona Activos; no se adivina"
        )
    mode = info.get("swap_mode")
    if mode not in SWAP_TYPES:
        raise Refused(
            f"{info['name']} cobra el swap en el modo {mode} de MT5, que SQX no expresa"
        )
    kind = SWAP_TYPES[mode]
    scale = info["point"] / tick if kind == "points" else 1
    long_, short = (
        (0, 0)
        if kind is None
        else (round(info["swap_long"] * scale, 6), round(info["swap_short"] * scale, 6))
    )
    swap = {
        "type": kind or "points",
        "long": long_,
        "short": short,
        "triple_swap_on": DAYS[info.get("swap_rollover3days", 3)],
        "rollout_hour": data["swap"]["rollout_hour"],
    }
    lines = [
        f"spread {spread} puntos de SQX = {info['spread']} puntos de {info['name']} "
        f"× {info['point']} (leído ahora en su servidor)",
        f"comisión {com['method']} {com['value']} (assets, {com.get('source') or 'sin fuente'})",
        f"swap {swap['type']} largo {long_} corto {short}, triple el "
        f"{swap['triple_swap_on'].lower()} (su servidor)",
        f"deslizamiento {slippage}: el tester de MT5 no desliza",
    ]
    stored = (data.get("mt5_point") or {}).get(firm, {}).get("point")
    if stored is not None and abs(stored - info["point"]) > 1e-12:
        lines.append(
            f"OJO: {info['name']} cotiza hoy con point {info['point']}, pero "
            f"assets/symbols/{data['symbol']}.yaml (mt5_point.{firm}) guarda {stored}: "
            "actualiza la ficha"
        )
    return (
        {
            "defaultSpread": spread,
            "defaultSlippage": slippage,
            "commission": {"method": com["method"], "value": com["value"]},
            "swap": swap,
        },
        lines,
    )
