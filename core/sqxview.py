"""The owner's «Export Data View» as SQStats keys: a databank's metrics with no SQX running."""

from pathlib import Path

import pandas as pd

from core import fanout, sqxfile, sqxstats

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
_FILES: dict[str, Path] = {}    # what frame() hands its forked children


def dof_ratio(trades: float, params: int) -> float:
    """The "DoF Ratio": in-sample trades per counted parameter, 0 when none."""
    return round(trades / params, 2) if params else 0


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
        `Param Count source` names where it came from; `DoF Ratio (IS)` is the IS trades
        over that count. SQX no longer carries either column.
    """
    global _FILES
    _FILES = files
    got = dict(fanout.run(_row, {name: 1 for name in files}, fanout.CORES))
    return pd.DataFrame([got[name] for name in files])


def _row(name: str) -> dict:
    """One strategy's row of frame(), read in a fanout child off the module's `_FILES`."""
    f = _FILES[name]
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
    # Both snippets were removed from the three installs on 2026-10-06 (they raised on
    # every WFM step and flooded the log), so a new strategy stores neither key: the
    # ratio is trades over the count above, for a strategy of any age.
    row["DoF Ratio (IS)"] = dof_ratio(row["# of trades (IS)"], row["Param Count (IS)"])
    return row


def measured(stats: dict[str, dict]) -> int:
    """Which of the two sample blocks this databank actually filled.

    Args:
        stats: Staged file stem to `sqxstats.stats()` of its main result.

    Returns:
        10 or 20. SQX fills the block its task is designated as and leaves the other at
        zero, and **which one that is cannot be assumed**: 🔬 measured 2026-09-23,
        `XAUUSD/SPP OOS` puts its retest numbers under (IS) and `XAU_ISOOS_ejemplo/OOS`
        puts them under (OOS). Taking the wrong one returns a column of zeros with nothing
        failing, so it is read off the data every time — on the metrics both blocks carry,
        since a structural one like `Param Count` holds a number whatever the task ran.

    Raises:
        SystemExit: Both blocks carry numbers, which means this databank was filled by a
            task that ran its own in/out split. Half its numbers would be dropped on a
            guess, so the gate refuses rather than picking.
    """
    paired = sorted({k for _, k in VIEW[10]} & {k for _, k in VIEW[20]})
    weight = {n: sum(abs(float(st.get(n, {}).get(k, 0))) for st in stats.values() for k in paired)
              for n in VIEW}
    filled = [n for n, w in weight.items() if w > 0]
    if len(filled) != 1:
        raise SystemExit(
            f"este databank llena {[LABEL[n] for n in filled] or 'ninguno'} de los dos bloques "
            f"de muestra, sobre {len(paired)} metricas pareadas {weight}. La puerta empareja "
            f"dos databanks de UNA ventana cada uno; uno que llena los dos corrio su propio "
            f"corte dentro y no se puede saber cual mitad es el retesteo")
    return filled[0]
