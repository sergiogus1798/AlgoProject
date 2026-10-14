"""MetaTracker's per-strategy equity series: cumulative net, drawdown in % of size, and the combined sum."""

from mt5.fleet.app import equity


def trade(magic: int, open_: int, close: int | None, net: float) -> dict:
    """A closed (or open) trade as `history.trades()` returns it."""
    return {"magic": magic, "open": open_, "close": close, "net": net}


def test_curves_and_combined() -> None:
    """Per-account curves keep one magic, drop accounts without it, and the combined line sums them."""
    a = {
        "login": 1,
        "name": "FTMO · Funded",
        "size": 10000,
        "trades": [
            trade(7, 0, 10, 100.0),
            trade(7, 20, 30, -300.0),
            trade(7, 40, 50, 50.0),
            trade(7, 60, None, 9.0),
            trade(8, 0, 5, 999.0),
        ],
    }
    b = {
        "login": 2,
        "name": "Hantec Trader · Fase 1",
        "size": 100000,
        "trades": [trade(7, 1, 12, 1000.0)],
    }
    c = {
        "login": 3,
        "name": "Sin trades",
        "size": 10000,
        "trades": [trade(8, 0, 5, 1.0)],
    }
    ca, cb = equity.curves([a, b, c], 7)
    assert [x["login"] for x in (ca, cb)] == [1, 2]
    assert ca["cum"] == [0, 100, -200, -150] and ca["trades"] == 3 and ca["net"] == -150
    assert abs(ca["win_rate"] - 2 / 3) < 1e-9
    assert abs(ca["max_dd"] - 3.0) < 1e-9  # 100 -> -200 on 10 000
    assert cb["pct"] == [0, 1.0] and cb["max_dd"] == 0
    both = equity.combined([ca, cb])
    assert both["times"] == [0, 1, 10, 12, 30, 50]
    assert both["cum"] == [0, 0, 100, 1100, 800, 850]
    assert abs(both["pct"][-1] - 100 * 850 / 110000) < 1e-9
