#!/usr/bin/env python3
"""Two databanks in, one joined cosecha out: the build window and the retest window."""

import argparse
import random
import shutil
import time
import zipfile
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from core import fanout, manifest, sqxfile
from core.paths import MASTER, databank_dir, export_dir, harvest_dir, worker_dir
from sqx.export import export_trades
from studies.screening.gate import collect, pairing

SAMPLE_SEED = 20260923      # a subset harvest is a sample, and a sample has to reproduce


def export(folder: Path, a: argparse.Namespace, databank: str, files: list[Path],
           packed: dict, install: Path, began: float) -> None:
    """Finish one databank's trade export beside the `trades.parquet` the harvest packed.

    Args:
        folder: `raw/<project>/<databank>/<day>`, already holding `trades.parquet`.
        a: The parsed arguments.
        databank: The databank those trades are of.
        files: Its .sqx, all of them.
        packed: What `tradepack.pack` counted.
        install: The install holding the project.
        began: When the harvest began (the manifest is dated then, as `export_trades` does).

    The three files `sqx.export.export_trades` leaves, with its manifest: every reader of a
    databank's export, and the loader's freshness check, find what that command writes.
    """
    feeds = {f.stem: sqxfile.symbol(f) for f in files}
    (folder / "timeframes.csv").write_text("strategy,timeframe\n" + "".join(
        f"{name},{fed.rsplit('_', 1)[-1]}\n" for name, (_, fed) in sorted(feeds.items())))
    ids = collect.identities(files)
    (folder / "identity.csv").write_text("strategy,identity\n" + "".join(
        f"{f.stem},{ids[f]}\n" for f in sorted(files)), encoding="utf-8")
    export_trades.lineage(a.project, databank, install, files[0].parent, folder)
    symbol, fed = next(iter(feeds.values()))
    feed = f"{symbol}_{fed.split('_LOM_')[0]}"
    manifest.write(folder,
                   {"install": str(install), "project": a.project, "databank": databank,
                    "symbol": feed},
                   f"export_trades.py --project {a.project} --databank {databank} "
                   f"--symbol {feed}",
                   {**packed, "timeframes": sorted({fed.rsplit("_", 1)[-1]
                                                    for _, fed in feeds.values()})}, since=began)
    print(f"wrote {folder}")


def whole_sides(a: argparse.Namespace, taken: dict[str, list[Path]], install: Path) -> dict[str, Path]:
    """Side to the export folder it will write: only the sides the pairing took whole (with `--exports`).

    A databank's export holds ALL its strategies: a side the pairing left some out of (unpaired, a
    `--limit` sample, or two files of one identity that `collect.index` collapsed) is not exported
    here and `export_trades` still does it, so «whole» counts the .sqx FILES, not identities.
    """
    return {side: export_dir(a.project, bank, date.today().isoformat())
            for side, bank in (("IS", a.databank), ("OOS", a.oos_databank))
            if a.exports and taken[side] and len(taken[side]) == len(list(
                databank_dir(a.project, bank, install).glob("*.sqx")))}


def set_aside(out: Path, identities: set) -> Path | None:
    """Move a same-day harvest of a DIFFERENT set of strategies out of the way before a new one.

    Args:
        out: The day folder about to be written (`core.paths.harvest_dir`).
        identities: The strategies the new harvest holds.

    Returns:
        Where the old one went, or None when there was nothing to move (no folder, or the same
        set, which is simply overwritten).

    It goes to `<databank>/_aparte/<day>.<HHMMSS>/`: two levels under the databank, so none of
    the readers that glob `<databank>/*/metrics.parquet`, `<project>/*/*/metrics.parquet` or
    `*/*/manifest.json` meets it, and "the newest" stays the day folder. Whoever wants it reads
    it by explicit path.
    """
    old = out / "metrics.parquet"
    if not old.exists() or set(pd.read_parquet(old, columns=[]).index) == set(identities):
        return None
    dest = out.parent / "_aparte" / f"{out.name}.{datetime.now():%H%M%S}"
    dest.parent.mkdir(exist_ok=True)
    shutil.move(str(out), dest)
    return dest


def problem_reasons(path: Path) -> str:
    """SQX's «Strategy Problems» reasons of a stored .sqx, `;`-joined; empty when none or unreadable."""
    try:
        return ";".join(sqxfile.strategy_problems(path)["reasons"])
    except (OSError, KeyError, zipfile.BadZipFile):
        return ""


def main() -> None:
    """Match the two databanks on identity, take both, and write the joined tables."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, help="the build databank, in sample")
    ap.add_argument("--oos-databank", required=True, help="the retest databank, out of sample")
    ap.add_argument("--role", help="worker role holding the project; the master if absent")
    ap.add_argument("--limit", type=int, default=0, help="a random sample of N pairs, for a trial")
    ap.add_argument("--exports", action="store_true",
                    help="write also each databank's own trade export (raw/), from the same "
                         "orderstocsv: what export_trades would write, without its two JVMs")
    a = ap.parse_args()
    began = time.time()

    install = worker_dir(a.role) if a.role else MASTER
    build = collect.index(databank_dir(a.project, a.databank, install))
    after = collect.index(databank_dir(a.project, a.oos_databank, install))
    # SQX drops a strategy from a retest databank when one of its own red flags fires there.
    # Those are decided, not missing: the gate carries them to the verdict as rejects.
    pairs, alias, missing = pairing.pair(build, after)
    matched = sorted(pairs)
    print(f"{a.databank}: {len(build)} · {a.oos_databank}: {len(after)} · "
          f"emparejadas por identidad {len(matched)} · mismo nombre e identidad distinta {len(alias)} · sin OOS {len(missing)} · "
          f"solo en OOS {len(set(after) - set(build) - set(alias))}")
    if alias:
        raise SystemExit(f"COSECHA PARADA: {len(alias)} estrategias del OOS comparten nombre con "
                         f"una del build y tienen otra identidad (nombre reutilizado o fichero "
                         f"reescrito); no se emparejan. Ver "
                         f"knowhow/sqx-format/names-reused-between-builds.md")
    if a.limit and a.limit < len(matched):
        matched = sorted(random.Random(SAMPLE_SEED).sample(matched, a.limit))

    out = harvest_dir(a.project, a.databank, date.today().isoformat())
    if (moved := set_aside(out, set(matched))):
        print(f"cosecha anterior de otro conjunto apartada en {moved}")
    out.mkdir(parents=True, exist_ok=True)
    taken = {side: [pairs[i][n] for i in matched] for n, side in enumerate(("IS", "OOS"))}
    whole = whole_sides(a, taken, install)
    for folder in whole.values():       # packed in place below: a kill mid-write must read stale, not fresh
        (folder / "manifest.json").unlink(missing_ok=True)
    sides = collect.tables(taken, out / "_work", whole)
    for side, folder in whole.items():
        export(folder, a, a.databank if side == "IS" else a.oos_databank, taken[side],
               sides[side]["packed"], install, began)
    metrics = sides["IS"]["metrics"].add_suffix(" [IS]").join(
        sides["OOS"]["metrics"].add_suffix(" [OOS]"))
    metrics = metrics.rename(columns={"Strategy Name [IS]": "strategy_build",
                                      "Strategy Name [OOS]": "strategy"})
    # The logic each strategy IS, with its parameter values ignored, so the redundancy
    # screen can ask whether N survivors are N ideas. Read from the files, not derived
    # from the numbers: 0.2 ms each.
    # Aligned on the index, never positionally: `metrics` comes back in SQX's own export
    # order and `matched` is sorted, so a list here would attach each shape to the wrong
    # strategy without anything failing.
    shapes = dict(fanout.run(sqxfile.structure, {pairs[i][1]: 1 for i in matched}, collect.WORKERS))
    metrics["structure"] = pd.Series({i: shapes[pairs[i][1]] for i in matched})
    metrics.to_parquet(out / "metrics.parquet", compression="zstd")
    trades = pd.concat([f["trades"].assign(sample=side) for side, f in sides.items()])
    trades.to_parquet(out / "trades.parquet", compression="zstd", index=False)
    equity = pd.concat([f["equity"].assign(sample=side) for side, f in sides.items()])
    equity.to_parquet(out / "equity.parquet", compression="zstd", index=False)
    problems = [problem_reasons(build[i]) for i in missing]
    pd.DataFrame({"identity": missing, "strategy_build": [build[i].stem for i in missing],
                  "StrategyProblems": problems}).to_csv(out / "missing_oos.csv", index=False)
    # 🔬 2026-10-11: on the stored harvests the build file's bitmask is 0 for every strategy
    # the retest dropped (SQX writes the reason on the retested file, which is gone), so a
    # missing twin cannot be told dismissed-with-reason from lost: the harvest does not stop.
    if (blind := sum(p == "" for p in problems)):
        print(f"ATENCION: {blind} ESTRATEGIAS SIN GEMELA OOS Y SIN MOTIVO LEGIBLE EN SU .SQX DE BUILD")

    blocks = {side: f["sample"] for side, f in sides.items()}
    print(f"bloque con datos: build={blocks['IS']} · retesteo={blocks['OOS']}")
    manifest.write(out,
                   {"install": str(install), "project": a.project, "databank": a.databank,
                    "oos_databank": a.oos_databank, "role": a.role or "master",
                    "metrics": "SQStats of each .sqx, the columns of «Export Data View» (collect.VIEW)",
                    "join": "identity (sha256 of strategy_Portfolio.xml), file name as fallback",
                    "sample_blocks": blocks},
                   f"python3 -m studies.screening.gate.harvest --project {a.project} --databank "
                   f"'{a.databank}' --oos-databank '{a.oos_databank}'",
                   {"build": len(build), "oos": len(after), "matched": len(matched),
                    "missing_oos": len(missing), "alias": len(alias), "trades": len(trades),
                    "equity_days": len(equity), "metrics_columns": len(metrics.columns)},
                   since=began)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
