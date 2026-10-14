"""The deployment package's pure parts: the file name that ties an EA to a firm and size, and the chart with its magic."""

from mt5.fleet import package


def test_name_and_chart() -> None:
    """The name carries firm and size; the chart carries symbol, period and the EA's magic."""
    assert package.stem("3.29.126", "FTMO", 100) == "Strategy_3_29_126_FTMO100k"
    got = package.chart("EURUSD.r", "H4", "Strategy_3_29_126_FTMO100k", 1001, 1)
    assert "symbol=EURUSD.r" in got and "period_type=1\r\nperiod_size=4" in got
    assert (
        "path=Experts\\AlgoProject\\Strategy_3_29_126_FTMO100k.ex5" in got
        and "MagicNumber=1001" in got
    )
