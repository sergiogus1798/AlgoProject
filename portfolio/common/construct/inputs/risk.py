"""A member's fixed-risk factor: the step-24 ATR stop's X, the sizing it scales, its floor lot."""

import zipfile
from pathlib import Path

import pandas as pd

from core.archive import read as archive_read
from sqx.inspect.strategymeta import settings
from sqx.variants.build import rewrite, stoploss


def sizing(identity: str, version: str) -> dict:
    """The member's fixed-risk factor, `f = atr_multiple / (risk_usd * x)`.

    SQX sizes every trade of the archived strategy at `risk_usd` over `atr_multiple` * ATR(20)
    (`ATRRiskBasedSizingFixedRisk`); at risk `r` of a balance `S` a member's P&L is SQX's own
    times `factor * r * S`.

    Args:
        identity: SHA-256 of the strategy's normalised XML.
        version: The archived version folder name.

    Returns:
        `x` (the grafted stop's ATR multiple, `sqx/variants/build/stoploss.graft`), `risk_usd`
        and `atr_multiple` (the money management's `Amount` and `ATRMult`), `min_size` (the
        smallest trade lot SQX drew, `harvest/trades.parquet`), `factor`.

    Raises:
        ValueError: The strategy carries no step-24 ATR stop (`StopLossCoef1` undeclared) --
            it was never sized for a fixed risk and cannot enter a funded search.
    """
    got = archive_read.load(identity, version)
    sqx_path = Path(got["sqx"])
    with zipfile.ZipFile(sqx_path) as z:
        portfolio = z.read(rewrite.PORTFOLIO).decode("utf-8", "replace")
    if stoploss.VARIABLE not in rewrite.declared(portfolio):
        raise ValueError("sin stop del paso 24")
    x = float(rewrite.values(portfolio)[stoploss.VARIABLE])

    node = settings.last_settings(sqx_path).find("RiskMoneyManagement/MoneyManagement")
    mm = settings.sizing(node)
    risk_usd = float(mm["params"]["Amount"])
    atr_multiple = float(mm["params"]["ATRMult"])

    trades = pd.read_parquet(Path(got["folder"]) / "harvest" / "trades.parquet")
    min_size = float(trades["Size"].min())
    return {"x": x, "risk_usd": risk_usd, "atr_multiple": atr_multiple, "min_size": min_size,
            "factor": atr_multiple / (risk_usd * x)}
