#!/usr/bin/env python3
"""The deep-MAE screen (encargo 27, step 8): how much of each strategy's result lives on trades
that went k ATR against and came back, over the gate's harvest. Chained after the gate's report."""

import argparse
import shutil
import time
from datetime import date

import pandas as pd

from core.manifest import write as write_manifest
from core.paths import report_dir
from core.study import output, result as envelope
from core.study.config import fingerprint
from ledger import record, study as studymod
from studies.screening.maeDepth import inputs, many, measures, one


def ledger_rows(
    a: argparse.Namespace,
    cfg: dict,
    timeframe: str,
    symbol: str,
    measured: pd.DataFrame,
    p: pd.DataFrame,
) -> list[dict]:
    """One row per segment read. It is a soft screen: n_out equals n_in (the marked are noted)."""
    rows = []
    for segment in sorted(measured["segment"].unique()):
        mine = pd.DataFrame(measured[measured["segment"] == segment])
        start, end = inputs.window(mine)
        rows.append(
            record.log(
                studymod.study_id(symbol, timeframe, a.family),
                {
                    "step": 8,
                    "launched_by": "studies.screening.maeDepth.report",
                    "config_hash": fingerprint(cfg),
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "segment": segment,
                    "window_from": start,
                    "window_to": end,
                    "n_in": len(p),
                    "n_out": len(p),
                    "criterion": "maeDepth/anomalous-recovered",
                    "thresholds": {
                        "k": cfg["depth"]["k"],
                        "sigma": cfg["anomaly"]["sigma"],
                        "min_cuota_rec": cfg["verdict"]["min_cuota_rec"],
                    },
                    "note": f"soft: {int(p['marcada'].sum())} marked of {len(p)}",
                },
            )
        )
    return rows


def show_cut(p: pd.DataFrame) -> None:
    """The duration cut per strategy and segment, before it is crossed with the MAE (§3)."""
    print(
        "corte de duración (media + sigma desviaciones, en barras) y cuántas operaciones lo pasan"
    )
    print(f"{'estrategia':<22}" + "".join(f"{s:>34}" for s in one.SEGMENTS))
    print(f"{'':<22}" + "   media  desv.  corte  n>=corte    n" * 2)
    for name, r in p.head(12).iterrows():
        print(
            f"{str(name):<22}"
            + "".join(
                f"{r[f'dur_mean_{s}']:>9.1f}{r[f'dur_std_{s}']:>7.1f}{r[f'dur_cut_{s}']:>7.1f}"
                f"{r[f'n_long_{s}']:>9d}{r[f'n_{s}']:>6d}"
                for s in one.SEGMENTS
            )
        )
    print(
        f"... {len(p)} estrategias; con corte > 0: "
        + ", ".join(
            f"{s} {int((p[f'n_long_{s}'].astype(int) > 0).sum())}" for s in one.SEGMENTS
        )
    )


def main() -> None:
    """Read the gate's harvest, measure every strategy by segment, write and record it."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument(
        "--databank", required=True, help="the build databank the gate ran on"
    )
    ap.add_argument("--feed", required=True, help="SQX feed name, e.g. USDJPY_M1")
    ap.add_argument(
        "--family",
        default="",
        help="the template family, for the ledger row; omitted, no row is written",
    )
    ap.add_argument(
        "--set", action="extend", nargs="+", default=[], help="section.key=value"
    )
    a = ap.parse_args()

    began = time.time()
    cfg = inputs.config(a.set)
    folder = inputs.newest(a.project, a.databank)
    envelope.progress(5, "leyendo la cosecha")
    data = inputs.load(folder, a.feed, cfg)
    envelope.progress(30, "midiendo MAE y duración")
    trades = data["trades"]
    measured = measures.per_trade(
        trades, data["index"], data["atr"], data["point_value"]
    )
    measured["identity"] = trades.loc[measured.index, "identity"].to_numpy()
    measured["segment"] = (
        trades.loc[measured.index, "sample"].map(inputs.SEGMENTS).to_numpy()
    )
    envelope.progress(60, "una lectura por estrategia")
    got = many.run(measured, data["names"], cfg)
    p = got["panel"]

    out = report_dir(a.project, a.databank, date.today().isoformat()) / "maeDepth"
    output.population(
        out,
        "maeDepth",
        got["population"],
        f"Criba del MAE profundo — {a.project} / {a.databank}",
    )
    shutil.rmtree(out / "estrategias", ignore_errors=True)
    for identity, name in data["names"].items():
        mine = pd.DataFrame(measured[measured["identity"] == identity])
        if len(mine):
            output.member(
                out,
                one.run(str(name), str(identity), mine, cfg),
                f"Criba del MAE profundo — {name}",
            )
    p.to_parquet(out / "panel.parquet", compression="zstd")
    p.reset_index().to_csv(
        out / "verdict.csv", columns=["strategy", "identity", "verdict"], index=False
    )
    write_manifest(
        out,
        {
            "project": a.project,
            "databank": a.databank,
            "feed": a.feed,
            "input": str((folder / "trades.parquet").resolve()),
        },
        f"python3 -m studies.screening.maeDepth.report --project {a.project} "
        f"--databank '{a.databank}' --feed {a.feed}",
        {"strategies": len(p), "marcadas": int(p["marcada"].sum())},
    )
    if a.family:
        ledger_rows(a, cfg, data["timeframe"], data["symbol"], measured, p)
    show_cut(p)
    envelope.progress(100, "hecho")
    bar = cfg["verdict"]["min_cuota_rec"]
    print(
        f"{len(p)} estrategias, {len(measured)} operaciones en {time.time() - began:.1f} s; "
        + (
            f"{int(p['marcada'].sum())} marcadas con cuota >= {bar}"
            if bar is not None
            else "sin umbral fijado: ninguna marcada"
        )
        + f"{'' if a.family else '; sin fila de ledger (falta --family)'} -> {out}"
    )


if __name__ == "__main__":
    main()
