#!/usr/bin/env python3
"""The walk forward correlation of one strategy's parameter grid, as a result and a verdict."""

import argparse
import json
import shutil
import time
from pathlib import Path

import pandas as pd

from core import assetdata
from core.study import output, result as envelope
from core.study.config import fingerprint
from engines.variants import look, panel
from studies.optimisation.wfc.contract import criteria, wfc
from studies.optimisation.wfc.inputs import config
from studies.optimisation.wfc.measure import correlation, persistence

MODULE = "studies.optimisation.wfc"
STEP = 17
EXTS = ("json", "html", "md")


def chosen(a: argparse.Namespace, cfg: dict) -> tuple[tuple, tuple]:
    """The composition this run reads: the flags, a named shortcut, or config.yaml's.

    Args:
        a: The parsed command line.
        cfg: The loaded config.

    Returns:
        What `engines.variants.panel.composition` returned.
    """
    if a.inside:
        return panel.composition(a.inside.split(","), a.outside.split(","))
    return panel.SHORTCUTS[a.split or cfg["split_mode"]]


def measured(kept: pd.DataFrame, cols: dict, days: pd.DataFrame, symbol: str, cfg: dict) -> dict:
    """The criteria metrics of one composition (`measure.persistence.measure`).

    Args:
        kept: The usable points under the composition.
        cols: What `panel.columns` returned for it.
        days: `panel.panel(work, "D")`: daily profit, one column per variant.
        symbol: The asset, whose declared segments cut the out-of-sample days.
        cfg: The loaded config.
    """
    asset = assetdata.load(symbol)
    starts = [pd.Timestamp(assetdata.segment_start(asset, s)) for s in panel.SEGMENTS]
    ends = starts[1:] + [pd.Timestamp.max]
    when = pd.to_datetime(days.index)
    out = pd.Series(False, index=days.index)
    for segment in cols["oos_label"].split("+"):
        at = panel.SEGMENTS.index(segment)
        out |= (when >= starts[at]) & (when < ends[at])
    sharpe = [kept.get(f"SharpeRatio ({cols[k]})", pd.Series(float("nan"), index=kept.index))
              for k in ("is_label", "oos_label")]
    return persistence.measure(
        kept[cols["is"]].to_numpy(float), kept[cols["oos"]].to_numpy(float),
        sharpe[0].to_numpy(float), sharpe[1].to_numpy(float),
        days.loc[out.to_numpy(), kept["variant_id"].astype(str)].to_numpy(float),
        cfg["persistence"]["top"], cfg["persistence"]["keep"], cfg["sharpe_floor"])


def parse() -> argparse.Namespace:
    """The command line: the batch, the family, and which composition of the split."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path,
                    help="the batch directory: holds metrics.parquet (contract C3)")
    ap.add_argument("--family", required=True,
                    help="la familia de plantillas del lote: la tercera parte del estudio del "
                         "ledger, donde se apunta cada composición leída")
    ap.add_argument("--inside", help="tramos dentro de muestra: build o build,oos1")
    ap.add_argument("--outside", help="tramos fuera de muestra: lo que queda — oos1, oos2 o "
                                      "oos1,oos2 con --inside build; oos2 con build,oos1")
    ap.add_argument("--split", choices=sorted(panel.SHORTCUTS),
                    help="atajo con nombre: `oos1_oos2` = IS build, OOS oos1+oos2; "
                         "`oos2_only` = IS build+oos1, OOS oos2. Por defecto, config.yaml")
    ap.add_argument("--set", dest="overrides", action="extend", nargs="+", default=[])
    a = ap.parse_args()
    if bool(a.inside) != bool(a.outside) or (a.inside and a.split):
        ap.error("--inside y --outside van juntos, y excluyen --split")
    return a


def main() -> None:
    """Ask the door, measure every offered partition, say what the requested one licenses."""
    a = parse()
    started = time.time()
    cfg = config.load(a.overrides)
    comp = chosen(a, cfg)
    name = panel.label(comp)
    symbol, timeframe = look.market(a.work)
    look.admit(STEP, comp[0] + comp[1], symbol)
    cols = panel.columns(comp)
    envelope.progress(20, f"{symbol} {timeframe}: IS={cols['is_label']}, "
                          f"OOS={cols['oos_label']}, permitidos por el ledger")
    metrics = pd.read_parquet(a.work / "metrics.parquet")
    kept = panel.points(metrics, cfg["min_trades"], cols)
    dropped = len(metrics) - len(kept)
    envelope.progress(55, f"{len(kept)} puntos utiles de {len(metrics)}")
    found = correlation.correlation(kept, cols)
    said = correlation.verdict(found, cfg["rho_floor"])
    thin = json.loads((a.work / "collected.json").read_text(encoding="utf-8"))
    # Every partition the ledger's door allows today (feedback §8.2): a human may switch
    # between them in the window with no new computation, so they all ride in this same
    # result — none of them logged to the ledger except the one actually requested, below.
    parts, metered, days = [], {}, panel.panel(a.work, "D")
    for other in panel.COMPOSITIONS:
        try:
            look.admit(STEP, other[0] + other[1], symbol)
        except PermissionError:
            continue
        other_cols = panel.columns(other)
        other_kept = panel.points(metrics, cfg["min_trades"], other_cols)
        other_found = correlation.correlation(other_kept, other_cols)
        other_said = correlation.verdict(other_found, cfg["rho_floor"])
        parts.append((panel.label(other), other_kept, other_found, other_said, other_cols,
                     len(metrics) - len(other_kept), len(metrics)))
        metered[other] = measured(other_kept, other_cols, days, symbol, cfg)
    # The top's persistence is read with build in sample against each later segment alone.
    windows = {c[1][0]: m for c, m in metered.items() if c[0] == ("build",) and len(c[1]) == 1}
    fabricated = thin.get("thin", 0) + len(metrics)
    note = (f"De {fabricated} combinaciones fabricadas, {thin.get('thin', 0)} se excluyeron al "
            f"recoger el lote por no llegar a {thin.get('floor', '?')} operaciones en todo el "
            f"periodo: el beneficio de una combinación que apenas opera mide una o dos "
            f"operaciones. Después, cada partición descarta además las que operan menos de "
            f"{cfg['min_trades']} en el tramo IS o en el OOS.")
    title = f"WFC — {a.work.name.replace('_', ' ')} — {cols['is_label']} contra {cols['oos_label']}"
    top = wfc.tab(parts, name, cfg["rho_floor"], note, cfg["min_trades"], cfg["sharpe_floor"])
    top["blocks"][-2:-2] = criteria.tables(           # before the correlations table and strata
        windows, {panel.label(c): m for c, m in metered.items()},
        cfg["persistence"]["top"], cfg["persistence"]["keep"])
    result = envelope.envelope(MODULE, a.work.name, None, cfg, started, [top],
                               wfc.verdict(said, found), glossary=wfc.GLOSSARY,
                               summary=criteria.summary(windows, metered[comp]))
    # One file set per composition, so a second reading never overwrites the first; the
    # plain `wfc.*` is a copy of the newest, which the viewer and step 20 read.
    out = a.work / "estudios"
    output.population(out, f"wfc_{name}", result, title,
                      f"{cols['is_label']} contra {cols['oos_label']}.")
    for ext in EXTS:
        shutil.copyfile(out / f"wfc_{name}.{ext}", out / f"wfc.{ext}")
    # The pipeline's own contract: pipeline/stages/verdict.py reads its scalars.
    (a.work / "wfc.json").write_text(
        json.dumps({**found, **said, "dropped": dropped,
                    "dropped_thin": thin.get("thin", 0), "composition": name,
                    "in_sample": cols["is_label"], "out_of_sample": cols["oos_label"]},
                   indent=2), encoding="utf-8")
    look.log(a.work, a.family, {
        "step": STEP, "launched_by": "wfc", "config_hash": fingerprint(cfg),
        "n_in": len(metrics), "n_out": len(metrics), "criterion": f"wfc/{name}",
        "thresholds": {k: cfg[k] for k in ("rho_floor", "min_trades")},
        "note": f"{said['call']} rho {found['rho']:.3f} sobre {len(kept)} puntos"},
             comp[0] + comp[1])
    envelope.progress(100, f"rho {found['rho']:.2f} — {said['call']} ({len(kept)} puntos; "
                           f"{thin.get('thin', 0)} fuera por pocas operaciones en total, "
                           f"{dropped} por pocas en un lado); "
                           f"{len(comp[0] + comp[1])} filas en el ledger del paso {STEP}")
    print(f"\n{said['why']}\n-> {out / f'wfc_{name}.html'}")


if __name__ == "__main__":
    main()
