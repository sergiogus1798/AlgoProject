"""A prop firm's conditions for one symbol, read off its own MT5 account and put in SQX's units."""
from mt5 import live

# MT5's ENUM_SYMBOL_SWAP_MODE → SQX's <Swap type>. The ones left out (swap in the base or the
# margin currency, reopen modes) have no SQX equivalent: a firm quoting one is refused.
SWAP_TYPES = {0: None, 1: "points", 4: "money", 5: "percent", 6: "percent"}
# MT5 numbers the triple-swap day from Sunday = 0; SQX spells it.
DAYS = ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"]


class Refused(Exception):
    """This firm cannot be priced for this symbol; the message says why, in Spanish."""


def read(symbol: str, account: dict) -> dict:
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
    info = live.ask("symbol", {"symbol": symbol}, account)
    if not isinstance(info, dict) or "error" in info or info.get("point") is None:
        raise Refused(f"MT5 no da {symbol} en {account['server']}: {info}")
    held = live.ask("account", {}, account)
    if not isinstance(held, dict) or held.get("login") != account["login"]:
        raise Refused(f"el terminal no entró en la cuenta {account['login']} de "
                      f"{account['server']}: {held}")
    first = live.ask("first", {"symbol": symbol}, account)
    return {**info, "account_leverage": held["leverage"], "account_currency": held["currency"],
            "first_bar": first.get("first") if isinstance(first, dict) else None}


def for_sqx(data: dict, firm: str, info: dict, slippage: float) -> tuple[dict, list[str]]:
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
        raise Refused(f"{data['symbol']} no tiene comisión confirmada de {firm} en "
                      f"assets/symbols/{data['symbol']}.yaml (costs.commission.brokers.{firm}): "
                      "complétala en la zona Activos; no se adivina")
    mode = info.get("swap_mode")
    if mode not in SWAP_TYPES:
        raise Refused(f"{info['name']} cobra el swap en el modo {mode} de MT5, que SQX no expresa")
    kind = SWAP_TYPES[mode]
    scale = info["point"] / tick if kind == "points" else 1
    long_, short = ((0, 0) if kind is None else
                    (round(info["swap_long"] * scale, 6), round(info["swap_short"] * scale, 6)))
    swap = {"type": kind or "points", "long": long_, "short": short,
            "triple_swap_on": DAYS[info.get("swap_rollover3days", 3)],
            "rollout_hour": data["swap"]["rollout_hour"]}
    lines = [f"spread {spread} puntos de SQX = {info['spread']} puntos de {info['name']} "
             f"× {info['point']} (leído ahora en su servidor)",
             f"comisión {com['method']} {com['value']} (assets, {com.get('source') or 'sin fuente'})",
             f"swap {swap['type']} largo {long_} corto {short}, triple el "
             f"{swap['triple_swap_on'].lower()} (su servidor)",
             f"deslizamiento {slippage}: el tester de MT5 no desliza"]
    return ({"defaultSpread": spread, "defaultSlippage": slippage,
             "commission": {"method": com["method"], "value": com["value"]}, "swap": swap},
            lines)
