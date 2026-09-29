"""The owner's «Export Data View» as SQStats keys: a databank's metrics with no SQX running."""

from pathlib import Path

import pandas as pd

from core import sqxfile, sqxstats

# The owner's «Export Data View», column for column, in its order, as SQStats keys: the
# metrics are read off each .sqx instead of exported through a conductor cycle. 🔬 2026-09-27,
# USDJPY_emaCross_H1 Results/OOS (100 + 32 strategies): every column equal to the view's
# export within 6e-8 relative (float32), except `R Expectancy`, which the view rounds to two
# decimals. Sample type 10 carries the (IS) block and 20 the (OOS) one; each emits its own set.
VIEW = {10: [("Net profit", "NetProfit"), ("# of trades", "NumberOfTrades"),
             ("Profit factor", "ProfitFactor"), ("Sharpe Ratio", "SharpeRatio"),
             ("Sortino Ratio", "SortinoRatio"), ("R Expectancy", "RExpectancy"),
             ("Winning Percent", "WinningPct"), ("Stability", "Stability"),
             ("Drawdown", "Drawdown"), ("Ret/DD Ratio", "ReturnDDRatio"),
             ("CAGR/Max DD %", "AnnualPctReturnDDRatio?"),
             ("CalmarRatio", "AnnualPctReturnDDRatio?"), ("DoF Ratio", "DoFRatio"),
             ("Max DD %", "DrawdownPct"), ("PSR", "ProbSharpeRatio"), ("RSquared", "RSquared"),
             ("SQN", "SQN"), ("TRL Ratio", "TRLRatio"), ("Ulcer Index %", "UlcerIndex"),
             ("ZScore", "ZScore"), ("Param Count", "ParameterCount")],
        20: [("Annual % Return", "AHPR"), ("CAGR/Max DD %", "AnnualPctReturnDDRatio?"),
             ("CalmarRatio", "AnnualPctReturnDDRatio?"), ("Net profit", "NetProfit"),
             ("PSR", "ProbSharpeRatio"), ("Profit factor", "ProfitFactor"),
             ("Ret/DD Ratio", "ReturnDDRatio"), ("SQN", "SQN"), ("Sharpe Ratio", "SharpeRatio"),
             ("Sortino Ratio", "SortinoRatio"), ("Winning Percent", "WinningPct"),
             ("Ulcer Index %", "UlcerIndex"), ("ZScore", "ZScore")]}
LABEL = {10: "(IS)", 20: "(OOS)"}


def frame(files: dict[str, Path]) -> pd.DataFrame:
    """The view's export of a databank, rebuilt from the files: what `metrics.csv` holds.

    Args:
        files: Strategy name to its .sqx.

    Returns:
        One row per strategy: `Strategy Name`, `Filters result` (SQX's own filter note, empty
        when no task filtered it; the readers drop text columns anyway), `TimeFrame (IS)`,
        then every column of both sample blocks with its ` (IS)`/` (OOS)` suffix, as the view
        emits them — the block a task did not fill carries SQX's zeros. `Param Count (IS)` is
        overwritten with `sqxfile.param_count(f)` (OPEN #17: SQX's own value is frozen at
        whichever `compute()` first ran under, often the old, inflated definition), and
        `Param Count source` names where it came from.
    """
    rows = []
    for name, f in files.items():
        st = sqxstats.stats(f)
        row = {"Strategy Name": name, "Filters result": sqxfile.sqx_filter(f) or "",
               "TimeFrame (IS)": sqxfile.symbol(f)[1].rsplit("_", 1)[-1]}
        for block, cols in VIEW.items():
            row.update({f"{col} {LABEL[block]}": st.get(block, {}).get(key, 0) for col, key in cols})
        # SQX freezes ParameterCount into the result it was computed under and never
        # recomputes it (OPEN #17): every strategy built before 2026-09-06 still carries the
        # old, inflated count. Replaced with the Python mirror off the definition itself
        # (core.sqxfile.param_count), right for a strategy of any age; `Param Count source`
        # says so rather than passing the number off as SQX's own.
        row["Param Count (IS)"] = sqxfile.param_count(f)
        row["Param Count source"] = "python (core.sqxfile.param_count)"
        rows.append(row)
    return pd.DataFrame(rows)
