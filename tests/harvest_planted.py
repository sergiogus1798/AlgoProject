"""A project's harvests, exports, reports and variant batch planted in a temporary data root: shared by the
`test_ui_*` and `test_identity` tests, not a test itself.

`plant()` must run before anything imports `core.paths` (it sets ALGO_DATA_ROOT, which that module reads
once): `import harvest_planted; harvest_planted.plant()` right after the `sys.path.insert` line. Nothing is
read from the machine's `AlgoData` except the market `bars/`, which the temp root links to (a server such as
gorilla holds only those). Everything else is synthetic and deterministic (fixed seeds, a few KB of
parquet generated here, no strategy of the owner's in git; rule 7):

- `PROJECT` (USDJPY M30, retired): harvests of 2026-09-27 (the three `sqx_synthetic` strategies, with their
  real `.sqx` kept under `raw/.../SPP_IS/`) and 2026-09-29 (`NAMES`, the one the routes read) holding
  metrics, trades and daily equity; the exports of the same day; the registry row; the gate on two days;
  the IS/OOS report and the cross-market report with one partial re-run.
- `NO_ASSET`: a two-strategy harvest of a project whose name says no asset.
- `LOTE` (NIKKEI225 M30): one harvest and one variant batch of `MOTHER`, the rest of `NAMES_LOTE` with none.
"""

import atexit
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

PROJECT = "Test_USDJPY_donchianUpperCrossUp_M30"
LOTE = "Trade_NIKKEI225_M30_volatilidadL"
DAY = "2026-09-29"
OLD_DAY = "2026-09-27"
LOTE_DAY = "2026-10-04"
NAMES = [
    "Strategy 13.14.82",
    "Strategy 9.13.86",
    "Strategy 5.16.75",
    "Strategy 17.10.56",
    "Strategy 4.8.54",
    "Strategy 21.7.50",
]
NO_ASSET = "XAU_ISOOS_ejemplo"  # a project whose name holds no asset symbol
MOTHER = "Strategy 10.11.484"  # the NIKKEI225 mother that has a variant batch
NAMES_LOTE = [MOTHER, "Strategy 3.2.100", "Strategy 5.9.200"]
ISOOS_NAME = NAMES[1]  # the strategy of the IS/OOS report
CROSS_NAME = (
    NAMES[0] + "(1)"
)  # the strategy of the cross-market report: a retest copy of the first one
MARKETS = [
    "USDJPY_DukasM1_the5ers",
    "EURUSD_DukasM1_the5ers",
    "GBPUSD_DukasM1_the5ers",
]
VARIANTS, AXES = 24, 8  # the planted batch: variants and varying parameters
FEED = MARKETS[0]
IS_SPAN = ("2008-01-07", "2017-12-29")
OOS_SPAN = ("2018-01-02", "2022-12-28")

METRICS = [  # the columns of the real harvest's metrics.parquet, in its order
    "TimeFrame [IS]",
    "Net profit [IS]",
    "# of trades [IS]",
    "Profit factor [IS]",
    "Sharpe Ratio [IS]",
    "Sortino Ratio [IS]",
    "R Expectancy [IS]",
    "Winning Percent [IS]",
    "Stability [IS]",
    "Drawdown [IS]",
    "Ret/DD Ratio [IS]",
    "CAGR/Max DD % [IS]",
    "CalmarRatio [IS]",
    "DoF Ratio [IS]",
    "Max DD % [IS]",
    "PSR [IS]",
    "RSquared [IS]",
    "SQN [IS]",
    "TRL Ratio [IS]",
    "Ulcer Index % [IS]",
    "ZScore [IS]",
    "Param Count [IS]",
    "Annual % Return [OOS]",
    "CAGR/Max DD % [OOS]",
    "CalmarRatio [OOS]",
    "Net profit [OOS]",
    "PSR [OOS]",
    "Profit factor [OOS]",
    "Ret/DD Ratio [OOS]",
    "SQN [OOS]",
    "Sharpe Ratio [OOS]",
    "Sortino Ratio [OOS]",
    "Winning Percent [OOS]",
    "Ulcer Index % [OOS]",
    "ZScore [OOS]",
]


def identity_of(name: str) -> str:
    """The planted identity of a strategy of `NAMES` or `NAMES_LOTE` (a hash of its name)."""
    return hashlib.sha256(f"planted|{name}".encode()).hexdigest()


def _base_root() -> Path:
    """The data root the process would have used without the plant: where the market bars live."""
    if os.environ.get("ALGO_DATA_ROOT"):
        return Path(os.environ["ALGO_DATA_ROOT"])
    cfg = Path(__file__).resolve().parent.parent / "config" / "machine.yaml"
    return Path(
        yaml.safe_load(cfg.read_text(encoding="utf-8"))["data_root"]
    ).expanduser()


def _trades(seed: int, span: tuple[str, str], n: int, price: float) -> pd.DataFrame:
    """`n` trades on the M30 grid of the weekdays in `span`: Buy, held 2..20 bars, mean P&L above zero."""
    rng = np.random.default_rng(seed)
    days = pd.bdate_range(*span)
    opened = days[np.sort(rng.integers(0, len(days), n))] + pd.to_timedelta(
        rng.integers(2, 40, n) * 30, unit="min"
    )
    closed = opened + pd.to_timedelta(rng.integers(2, 20, n) * 30, unit="min")
    pnl = np.round(rng.normal(25.0, 150.0, n), 2)
    entry = np.round(price + rng.normal(0, 3, n), 3)
    return pd.DataFrame(
        {
            "Type": pd.Categorical(["Buy"] * n),
            "Open time": opened,
            "Open price": entry,
            "Size": np.round(rng.uniform(0.5, 2.5, n), 2),
            "Close time": closed,
            "Close price": np.round(entry + pnl / 100.0, 3),
            "Profit/Loss": pnl,
            "Balance": 100000.0 + np.cumsum(pnl),
            "Sample type": "",
            "Close type": pd.Categorical(
                rng.choice(["Exit After X Bars", "Stop Loss", "Profit Target"], n)
            ),
            "MAE ($)": -np.abs(np.round(rng.normal(300, 150, n), 2)),
            "MFE ($)": np.abs(np.round(rng.normal(300, 150, n), 2)),
        }
    ).sort_values("Open time", ignore_index=True)


def harvest(
    folder: Path, names: list[str], seed: int, price: float, project: str
) -> None:
    """One harvest day: metrics (indexed by identity), IS+OOS trades, daily equity and the manifest."""
    folder.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    ids = [identity_of(n) for n in names]
    metrics = pd.DataFrame(
        rng.uniform(0.1, 5.0, (len(names), len(METRICS))),
        columns=METRICS,
        index=pd.Index(ids, name="identity"),
    )
    metrics["TimeFrame [IS]"] = "M30"
    metrics["# of trades [IS]"] = 100
    metrics.insert(0, "strategy_build", names)
    metrics["strategy"] = names
    metrics["structure"] = [hashlib.sha256(n.encode()).hexdigest() for n in names]
    metrics.to_parquet(folder / "metrics.parquet")
    trades, equity = [], []
    for k, ident in enumerate(ids):
        for sample, span, n in (("IS", IS_SPAN, 80), ("OOS", OOS_SPAN, 40)):
            t = _trades(seed * 100 + k * 2 + (sample == "OOS"), span, n, price)
            t["Sample type"] = pd.Categorical(["IST" if sample == "IS" else "OOS"] * n)
            t["identity"], t["sample"] = ident, sample
            trades.append(t)
            days = pd.bdate_range(span[0], span[1])
            earned = t.groupby(t["Close time"].dt.normalize())["Profit/Loss"].sum()
            curve = earned.reindex(days, fill_value=0.0).cumsum()
            equity.append(
                pd.DataFrame(
                    {
                        "day": days,
                        "identity": ident,
                        "equity": curve.to_numpy(),
                        "sample": sample,
                    }
                )
            )
    pd.concat(trades, ignore_index=True).to_parquet(folder / "trades.parquet")
    pd.concat(equity, ignore_index=True).to_parquet(folder / "equity.parquet")
    manifest = {
        "date": folder.name,
        "source": {
            "project": project,
            "databank": "Results",
            "oos_databank": "OOS",
            "sample_blocks": {"IS": "(IS)", "OOS": "(OOS)"},
        },
        "counts": {"build": len(names), "oos": len(names), "matched": len(names)},
    }
    (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def export(
    folder: Path,
    names: list[str],
    seed: int,
    bank: tuple[str, str],
    markets: list[str] | None = None,
) -> None:
    """An export day as the exporters leave it: `trades.parquet` (strategy, and Symbol per market) and its manifest."""
    folder.mkdir(parents=True, exist_ok=True)
    parts = []
    for k, name in enumerate(names):
        for j, market in enumerate(markets or [None]):
            t = _trades(seed + 10 * k + j, IS_SPAN, 30, 110.0)
            t["Sample type"] = pd.Categorical(["IST"] * len(t))
            t["strategy"] = pd.Categorical([name] * len(t))
            if market:
                t["Symbol"] = market
            parts.append(t)
    pd.concat(parts, ignore_index=True).to_parquet(folder / "trades.parquet")
    source = {"project": bank[0], "databank": bank[1], "timeframes": ["M30"]}
    (folder / "manifest.json").write_text(
        json.dumps(
            {
                "date": folder.name,
                "source": source,
                "counts": {"strategies": len(names)},
            }
        ),
        encoding="utf-8",
    )


def write(path: Path, doc: dict[str, Any]) -> None:
    """Write one JSON file, making its folder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")


def _batch(root: Path) -> None:
    """The variant batch of `MOTHER`: `VARIANTS` rows (the first is the origin), `AXES` varying parameters."""
    rng = np.random.default_rng(7)
    frame = pd.DataFrame(
        {
            "variant_id": [f"P{k:05d}" for k in range(VARIANTS)],
            **{
                f"param_Axis{a}": rng.uniform(1, 50, VARIANTS).round(2)
                for a in range(AXES)
            },
            "stratum": ["origin"] + ["factorial"] * (VARIANTS - 1),
            "origin": [True] + [False] * (VARIANTS - 1),
            "NetProfit (build)": rng.normal(1000, 400, VARIANTS),
            "NetProfit (oos1)": rng.normal(300, 400, VARIANTS),
            "NetProfit (oos2)": rng.normal(100, 400, VARIANTS),
        }
    )
    folder = root / "strategyPermutations" / LOTE / MOTHER.replace(" ", "_")
    folder.mkdir(parents=True)
    frame.to_parquet(folder / "metrics.parquet")


def _sqx(root: Path) -> list[str]:
    """The three synthetic `.sqx` under `raw/.../SPP_IS/<old day>/strategies/` and the old harvest naming them.

    Returns:
        Their identities, in `sqx_synthetic.NAMES` order.
    """
    import sqx_synthetic
    from core import sqxfile

    kept = root / "raw" / PROJECT / "SPP_IS" / OLD_DAY
    files = sqx_synthetic.databank(kept / "strategies")
    write(
        kept / "spp" / "manifest.json",
        {"date": OLD_DAY, "source": {"project": PROJECT, "databank": "SPP IS"}},
    )
    ids = [sqxfile.identity(f) for f in files]
    folder = root / "harvest" / PROJECT / "Results" / OLD_DAY
    folder.mkdir(parents=True)
    names = list(sqx_synthetic.NAMES)
    pd.DataFrame(
        {"strategy_build": names, "strategy": names},
        index=pd.Index(ids, name="identity"),
    ).to_parquet(folder / "metrics.parquet")
    source = {"project": PROJECT, "databank": "Results", "oos_databank": "OOS"}
    write(folder / "manifest.json", {"date": OLD_DAY, "source": source})
    for databank, day_dir in (
        ("OOS", "OOS"),
        ("Retest Markets - Family", "Retest_Markets_-_Family"),
    ):
        write(
            root / "raw" / PROJECT / day_dir / OLD_DAY / "manifest.json",
            {"date": OLD_DAY, "source": {"project": PROJECT, "databank": databank}},
        )
    return ids


def plant() -> Path:
    """Build the project's folders in a fresh temp root, point ALGO_DATA_ROOT at it and return the root.

    Returns:
        The temporary data root; `bars/` in it is a link to the machine's market data.
    """
    base = _base_root()
    root = Path(tempfile.mkdtemp(prefix="algo-harvest-"))
    os.environ["ALGO_DATA_ROOT"] = str(root)
    atexit.register(
        shutil.rmtree, root, ignore_errors=True
    )  # unlinks `bars`, never follows it
    if (base / "bars").exists():
        (root / "bars").symlink_to(base / "bars")
    _sqx(root)
    harvest(root / "harvest" / PROJECT / "Results" / DAY, NAMES, 1, 110.0, PROJECT)
    export(root / "raw" / PROJECT / "Results" / DAY, NAMES, 5, (PROJECT, "Results"))
    export(
        root / "raw" / PROJECT / "Retest_Markets_-_Family" / DAY,
        NAMES[:2],
        50,
        (PROJECT, "Retest Markets - Family"),
        MARKETS,
    )
    (root / "reports" / PROJECT / "MCR_All" / DAY / "mcRetest").mkdir(
        parents=True
    )  # reported, held by no install
    harvest(
        root / "harvest" / LOTE / "Results" / LOTE_DAY, NAMES_LOTE, 2, 30000.0, LOTE
    )
    harvest(
        root / "harvest" / NO_ASSET / "Results" / DAY, NAMES[:2], 3, 110.0, NO_ASSET
    )
    import reports_planted

    reports_planted.plant_reports(root)
    _batch(root)
    rows = [
        "name,kind,install,created,purpose,symbol,timeframe,template,workflow,retired,archive,acceptance,family"
    ]
    rows += [
        f"{PROJECT},test,SQX_w2,2026-09-26 22:32,planted,USDJPY,M30,,yes,2026-09-30 07:06,,,",
        f"{LOTE},trade,SQX_w2,2026-10-01 10:00,planted,NIKKEI225,M30,,yes,2026-10-05 07:06,,,",
    ]
    (root / "projects").mkdir()
    (root / "projects" / "registry.csv").write_text(
        "\n".join(rows) + "\n", encoding="utf-8"
    )
    return root
