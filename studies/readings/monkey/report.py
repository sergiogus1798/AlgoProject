#!/usr/bin/env python3
"""The null study's command: every strategy of one export against its monkeys, or one alone."""

import argparse
import json
import time
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from core import assetdata, fanout
from core.archive.manifest import registry
from core.manifest import write as write_manifest
from core.paths import report_dir
from core.study import draws, identity, output
from core.study.render import markdown
from engines.nulls import inputs, model
from studies.readings.monkey import many, one


def additional_only(project: str, feeds: list[str]) -> list[str]:
    """The markets an in-sample (IST) monkey read may use: never the project's own.

    Owner, 2026-09-29: a random trader is compared only on the main market's OOS or on the
    additional markets, never on the build the strategy was selected on.

    Args:
        project: The project the export belongs to; its asset comes from projects/registry.csv.
        feeds: The markets the export holds.

    Returns:
        `feeds` without the project's own asset feeds.

    Raises:
        SystemExit: The project's asset is unknown, or only its own market is left.
    """
    try:
        symbol = registry(project).get("symbol")
    except KeyError:
        symbol = None
    if not symbol:
        raise SystemExit(f"{project} no está en projects/registry.csv: no se sabe cuál es su "
                         "mercado principal, así que no se lee IST (usa --sample OOS1)")
    own = set(assetdata.load(symbol).get("feeds") or [])
    kept = [f for f in feeds if f not in own]
    if not kept:
        raise SystemExit(f"IST en {symbol} es el build en el que se eligió la estrategia: el mono "
                         "sólo se lee ahí en OOS1 o en los mercados adicionales (dueño, 2026-09-29)")
    return kept


def sign(rows: list[dict], signed: dict) -> None:
    """Put each row's strategy identity on it, as nulls.csv does; unresolved stays empty."""
    for r in rows:
        r["identity"] = str(signed.get(r["strategy"]) or "")


def stamp(panel: pd.DataFrame, signed: dict, cfg: dict) -> None:
    """Add nulls.csv's identity, note and seed columns to the panel, in place."""
    panel.insert(0, "identity", panel.index.map(signed))
    panel.insert(1, "note", np.where(panel["identity"].isna(), identity.NOTE, ""))
    panel["seed"] = cfg["nulls"]["seed"]


def saved_source(out: Path) -> dict[str, Any]:
    """What the previous population run's manifest recorded, which `--only` must keep.

    Raises:
        SystemExit: There is no previous run in `out` to merge into.
    """
    try:
        source = json.loads((out / "manifest.json").read_text(encoding="utf-8"))["source"]
        int(source["seed"])
        return source
    except (OSError, KeyError, ValueError, TypeError) as err:
        raise SystemExit(f"--only completa una corrida previa y en {out} no hay ninguna con "
                         "manifest: corre primero la población entera") from err


def refuse_drift(saved: dict, now: dict) -> None:
    """Refuse `--only` when any field of how the nulls were drawn differs from the manifest's.

    Args:
        saved: The manifest's `source`.
        now: The same fields as this call computes them.

    Raises:
        SystemExit: Naming the first field that differs: rows computed two ways never share a nulls.csv.
    """
    for key, value in now.items():
        if saved.get(key) != value:
            raise SystemExit(f"--only: «{key}» difiere de la corrida guardada ({saved.get(key)!r} "
                             f"guardado, {value!r} ahora): dos cálculos distintos no van en un "
                             "mismo nulls.csv; corre la población entera")


def merged(out: Path, panel: pd.DataFrame) -> pd.DataFrame:
    """nulls.csv with `panel`'s strategies replaced and every other row kept, sorted as a full run is."""
    old = pd.read_csv(out / "nulls.csv", index_col=0)
    both = pd.concat([old[~old.index.isin(panel.index)], panel]).reset_index()
    return both.sort_values(["strategy", "market"], kind="stable").set_index("strategy")


def main() -> None:
    """Run one strategy, or every strategy of one export, through every rung."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--feed", default="",
                    help="SQX feed name, e.g. XAUUSD_M1. A one-market export "
                         "needs it; a cross-market export runs every market without it")
    ap.add_argument("--strategy", default="", help="one strategy, read in full; all when omitted")
    ap.add_argument("--timeframe", default="M30")
    ap.add_argument("--sample", default="OOS1",
                    help="OOS1 out of sample, IST in sample. IST is refused on the project's own "
                         "market -- the build the strategy was selected on (owner, 2026-09-29) "
                         "-- and kept only on the additional markets of a cross-market export, "
                         "where the strategy was never selected on either sample")
    ap.add_argument("--statistic", default="net",
                    help="with --strategy: which one the call and the channels read")
    ap.add_argument("--limit", type=int, default=0, help="first N strategies only, for a trial")
    ap.add_argument("--only", default="",
                    help="file of strategy names, one per line: run only those and merge them "
                         "into the previous run's nulls.csv and distributions, under that run's "
                         "root (a different --seed is refused)")
    ap.add_argument("--set", action="extend", nargs="+", default=[], help="section.key=value")
    ap.add_argument("--seed", type=int, default=None,
                    help="root of the monkeys' random streams; omitted, a fresh one is drawn. "
                         "Every run writes the one it used (manifest, nulls.csv): pass it back "
                         "to get the same p-values")
    ap.add_argument("--workers", type=int, default=fanout.CORES,
                    help="strategies run at once; each process holds one strategy's blocks")
    a = ap.parse_args()

    out = report_dir(a.project, a.databank, date.today().isoformat()) / "monkey"
    if a.only:
        saved = saved_source(out)
        root = int(saved["seed"])
        if a.seed not in (None, root):
            raise SystemExit(f"--only sigue con la semilla {root} de la corrida guardada: dos "
                             f"raíces en un mismo nulls.csv no (pedida {a.seed})")
        a.seed = root
    cfg = inputs.config(a.set + inputs.seeded(a.seed))
    packed = inputs.newest(a.project, a.databank)
    # A cross-market export names its markets in `Symbol`; a one-market one only in its
    # manifest, which is why --feed is its market.
    feeds = [a.feed] if a.feed else inputs.markets(packed)
    assert feeds, f"{packed} es de un solo mercado y no dice cuál: pásalo con --feed"
    if a.sample == "IST":
        feeds = additional_only(a.project, feeds)
    cfg["feed"] = " ".join(feeds)
    if a.only:
        refuse_drift(saved, {"feed": feeds, "timeframe": a.timeframe, "sample": a.sample,
                             "input": str(packed.resolve()), "draws": cfg["nulls"]["draws"],
                             "rungs": cfg["nulls"]["rungs"], "overrides": a.set})
    frames = {feed: inputs.bars(feed, a.timeframe) for feed in feeds}
    if a.strategy:
        assert len(feeds) == 1, "--strategy lee un mercado: di cuál con --feed"
        kept = []
        got = one.run(a.strategy, {"trades": inputs.sample(packed, a.strategy, a.sample, a.feed),
                                   "frame": frames[a.feed], "folder": packed.parent},
                     cfg, a.statistic, kept)
        # One strategy must not wipe the population's rows: replace only its own identity.
        ident = output.identify(packed.parent, [a.strategy])[a.strategy]
        sign(kept, {a.strategy: ident})
        draws.merge(out, kept, defer=True)
        title = f"Contra el mono — {a.strategy}"
        print(markdown.render(got, title))
        print(f"-> {output.member(out, got, title, f'Muestra {a.sample}.')}")
        return

    # One read and one split per market, where each strategy used to re-read the whole
    # export: the same rows in the same order as inputs.sample() returns them.
    sample = {(str(name), feed): rows
              for feed in feeds
              for name, rows in inputs.trades(packed, a.sample, feed).groupby(
                  "strategy", observed=True)}
    if a.limit:
        kept = sorted({name for name, _ in sample})[:a.limit]
        sample = {k: v for k, v in sample.items() if k[0] in kept}
    if a.only:
        names = set(Path(a.only).read_text(encoding="utf-8").split())
        if names - {name for name, _ in sample}:
            raise SystemExit(f"--only nombra estrategias que no están en el export: "
                             f"{sorted(names - {name for name, _ in sample})[:5]}")
        sample = {k: v for k, v in sample.items() if k[0] in names}
    got = many.run(sample, frames, cfg, a.workers)
    if a.only:
        signed = output.identify(packed.parent, sorted(set(got["panel"].index)))
        sign(got["draws"], signed)
        draws.merge(out, got["draws"])
        stamp(got["panel"], signed, cfg)
        whole = merged(out, got["panel"])
        whole.to_csv(out / "nulls.csv")
        output.population(out, "monkey", many.population(
            whole.drop(columns=["identity", "note", "seed"]), len(feeds), cfg, time.time()),
            f"Contra el mono — {a.project} / {a.databank}")
        print(f"{len(got['panel'])} pares fundidos en {out / 'nulls.csv'} ({len(whole)} en total), "
              f"semilla {cfg['nulls']['seed']}; resumen de población rehecho")
        return
    output.population(out, "monkey", got["population"],
                      f"Contra el mono — {a.project} / {a.databank}")
    signed = output.identify(packed.parent, sorted(set(got["panel"].index)))
    if identity.note(signed):
        print(identity.note(signed))
    sign(got["draws"], signed)
    draws.save(out, got["draws"])
    stamp(got["panel"], signed, cfg)
    got["panel"].to_csv(out / "nulls.csv")
    (out / "rungs.json").write_text(json.dumps(model.RANDOMISES, indent=2), encoding="utf-8")
    write_manifest(out,
                   {"project": a.project, "databank": a.databank, "sample": a.sample,
                    "feed": feeds, "timeframe": a.timeframe, "input": str(packed.resolve()),
                    "draws": cfg["nulls"]["draws"], "rungs": cfg["nulls"]["rungs"],
                    "seed": cfg["nulls"]["seed"], "overrides": a.set},
                   " ".join(["python3 -m studies.readings.monkey.report", "--project", a.project,
                             "--databank", a.databank, *(["--feed", a.feed] if a.feed else []),
                             "--timeframe", a.timeframe, "--sample", a.sample,
                             "--seed", str(cfg["nulls"]["seed"])]),
                   {"nulls.csv": len(got["panel"])})
    print(f"\n{len(got['panel'])} estrategias x mercado ({len(feeds)} mercados), "
          f"semilla {cfg['nulls']['seed']} -> {out}")


if __name__ == "__main__":
    main()
