"""The SQX side: the live strategies retested over one week in a Test_Reconcile project on the conductor. UNRUN."""

import json
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from core import assetdata, exportdrv, trades
from core.paths import ROOT
from mt5.reconcile import week as weeks
from mt5.verify import sqxside as verify_sqx
from sqx.projects import cfxio, mt5verify
from sqx.projects.wfc import declare, retitle
from ui.daemon.launch.run import assets as rule_five


def window(week: str, data: dict, warmup_days: int) -> tuple[str, str]:
    """The days the retest reads: the warm-up before the week's Monday, to its Sunday.

    Never past the day before SQX's last one: a range closing on SQX's last day reads
    «Project has unresolved resources» and never starts (📓 2026-09-30, `mt5.verify.run.latest`).
    ⚠️ So the week's last trading day is only read once the feed holds the day after it.
    """
    monday, after = weeks.bounds(week)
    last = date.fromisoformat(str(data["data"]["to"])[:10]) - timedelta(days=1)
    end = min((after - pd.Timedelta(days=1)).date(), last)
    if end < monday.date():  # pyright: ignore[reportOperatorIssue]  # pandas stubs: Timedelta/Timestamp unions with NaT
        raise SystemExit(
            f"SQX tiene datos hasta el {data['data']['to']}: la semana {week} "
            "todavía no está en los datos de desarrollo (weekly-data-update)"
        )
    return (monday - pd.Timedelta(days=warmup_days)).date().isoformat(), end.isoformat()  # pyright: ignore[reportAttributeAccessIssue]  # pandas stubs: Timedelta/Timestamp unions with NaT


def build(name: str, strategy: Path, asset: str, timeframe: str, cfg: dict) -> Path:
    """Clone the frozen donor into the week's Test_ project through the builder's own command
    (hard rules 6 and 10: its registry row, its checks). Returns the project.cfx."""
    argv = [
        sys.executable,
        "-m",
        "sqx.projects.builder",
        name,
        "--purpose",
        "weeklyReconciler: las estrategias en real de la semana, en SQX con "
        "los datos de desarrollo, para compararlas con la cuenta",
        "--template",
        str(strategy),
        "--symbol",
        asset,
        "--role",
        cfg["role"],
        "--timeframe",
        timeframe,
        "--tasks",
        "Retest",
        "--only",
        ",".join(cfg["donor_members"]),
        "--silence",
        "Retest",
        "--json",
    ]
    got = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=600)
    if got.returncode:
        raise SystemExit(
            f"el builder no creó {name}:\n{(got.stderr or got.stdout)[-2000:]}"
        )
    return Path(json.loads(got.stdout[got.stdout.index("{") :])["cfx"])


def configure(cfx: Path, data: dict, days: tuple[str, str], cfg: dict) -> None:
    """Make the donor's retest the week's backtest, the only active task.

    The task is `sqx.projects.mt5verify.write_task`'s: the asset's own costs of
    `cfg["segment"]` over `days`, no out-of-sample split, no cross-check, every acceptance
    silenced, a fixed lot. The project is not held by an install (hard rule 4).
    """
    members = cfxio.members(cfx)
    member = cfg["donor_members"][0]
    sizing = {"method": "FixedSize", "params": {"Size": cfg["lots"]}}
    members[member] = mt5verify.write_task(
        members[member].decode("utf-8"),
        data["sqx_symbol"],
        assetdata.sqx_settings(data, cfg["segment"]),
        days,
        (cfg["input"], cfg["output"]),
        sizing,
    ).encode("utf-8")
    config = re.sub(
        r'(<Task\b[^>]*?)active="true"',
        r'\g<1>active="false"',
        members["config.xml"].decode("utf-8"),
    )
    config = declare(
        retitle(config, member, cfg["task_title"]), [cfg["input"], cfg["output"]]
    )
    members["config.xml"] = config.encode("utf-8")
    with zipfile.ZipFile(cfx, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in members.items():
            z.writestr(name, blob)


def backtest(live: pd.DataFrame, week: str, cfg: dict, work: Path) -> pd.DataFrame:
    """Every live strategy's SQX trades over the week, one project per asset and timeframe.

    Args:
        live: Register rows with `strategy`, `identity`, `sqx`, `asset`, `timeframe`.
        week: "YYYY-Www".
        cfg: The `sqx` block of config.yaml.
        work: The week's folder; each project stages its strategies under `<project>/in`.

    Returns:
        Schema T plus `strategy` and `identity`, feed clock, warm-up trades included. The
        conductor is started and stopped by `mt5.verify.sqxside.run` (`core.worker`, only
        `action=status` between start and «Project finished», refused if someone has it
        up); each project is retired whatever happened (hard rule 6).
    """
    out = []
    once = live.drop_duplicates("strategy")  # one backtest serves every firm it runs on
    for (asset, timeframe), group in once.groupby(["asset", "timeframe"]):  # pyright: ignore[reportGeneralTypeIssues]  # pandas stubs: groupby key/index is Hashable
        rule_five(asset)
        data = assetdata.load(asset)
        days = window(week, data, cfg["warmup_days"])
        project = f"Test_Reconcile_{asset}_{timeframe}_{week.replace('-', '')}"
        files = [Path(p) for p in group["sqx"]]
        folder = work / project
        (folder / "in").mkdir(parents=True, exist_ok=True)
        for extra in files[1:]:  # run() stages the first; the load reads the folder
            shutil.copy2(extra, folder / "in" / extra.name)
        cfx = build(project, files[0], asset, timeframe, cfg)
        try:
            configure(cfx, data, days, cfg)
            banks = verify_sqx.run(
                project, cfg["role"], files[0], folder, {"week": cfg["output"]}, cfg
            )
            dest = folder / "csv"
            shutil.rmtree(dest, ignore_errors=True)
            if any(banks["week"].glob("*.sqx")):
                exportdrv.trades(banks["week"], dest)
            names = {Path(r.sqx).stem: r for r in group.itertuples()}  # pyright: ignore[reportAttributeAccessIssue]  # pandas stubs: itertuples rows lose their field names
            for csv in sorted(dest.glob("*.csv")):
                row = names[csv.stem]
                out.append(
                    trades.read(csv).assign(
                        strategy=row.strategy,  # pyright: ignore[reportAttributeAccessIssue]  # pandas stubs: itertuples rows lose their field names
                        identity=row.identity,  # pyright: ignore[reportAttributeAccessIssue]  # pandas stubs: itertuples rows lose their field names
                    )
                )
        finally:
            print(verify_sqx.retire(project, cfg["role"]), flush=True)
    return (
        pd.concat(out, ignore_index=True)
        if out
        else pd.DataFrame(
            columns=[
                "strategy",
                "identity",
                "Type",
                "Open time",
                "Open price",
                "Size",  # pyright: ignore[reportArgumentType]  # pandas/numpy stubs lose the type through indexing
                "Close time",
                "Close price",
                "Profit/Loss",
                "MAE ($)",
                "MFE ($)",
            ]
        )
    )
