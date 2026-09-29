#!/usr/bin/env python3
"""The null study's command: every strategy of one export against its monkeys, or one alone."""

import argparse
import json
from datetime import date

from core import assetdata, fanout
from core.archive.manifest import registry
from core.manifest import write as write_manifest
from core.paths import report_dir
from core.study import identity, output
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


def main() -> None:
    """Run one strategy, or every strategy of one export, through every rung."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--feed", default="",
                    help="SQX feed name, e.g. XAUUSD_DukasM1_Infinox. A one-market export "
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
    ap.add_argument("--set", action="extend", nargs="+", default=[], help="section.key=value")
    ap.add_argument("--workers", type=int, default=fanout.CORES,
                    help="strategies run at once; each process holds one strategy's blocks")
    a = ap.parse_args()

    cfg = inputs.config(a.set)
    packed = inputs.newest(a.project, a.databank)
    # A cross-market export names its markets in `Symbol`; a one-market one only in its
    # manifest, which is why --feed is its market.
    feeds = [a.feed] if a.feed else inputs.markets(packed)
    assert feeds, f"{packed} es de un solo mercado y no dice cuál: pásalo con --feed"
    if a.sample == "IST":
        feeds = additional_only(a.project, feeds)
    cfg["feed"] = " ".join(feeds)
    frames = {feed: inputs.bars(feed, a.timeframe) for feed in feeds}
    out = report_dir(a.project, a.databank, date.today().isoformat()) / "monkey"
    if a.strategy:
        assert len(feeds) == 1, "--strategy lee un mercado: di cuál con --feed"
        got = one.run(a.strategy, {"trades": inputs.sample(packed, a.strategy, a.sample, a.feed),
                                   "frame": frames[a.feed], "folder": packed.parent},
                     cfg, a.statistic)
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
    got = many.run(sample, frames, cfg, a.workers)
    output.population(out, "monkey", got["population"],
                      f"Contra el mono — {a.project} / {a.databank}")
    signed = output.identify(packed.parent, sorted(set(got["panel"].index)))
    if identity.note(signed):
        print(identity.note(signed))
    got["panel"].insert(0, "identity", got["panel"].index.map(signed))
    got["panel"].insert(1, "note", got["panel"]["identity"].isna().map({True: identity.NOTE,
                                                                        False: ""}))
    got["panel"].to_csv(out / "nulls.csv")
    (out / "rungs.json").write_text(json.dumps(model.RANDOMISES, indent=2), encoding="utf-8")
    write_manifest(out,
                   {"project": a.project, "databank": a.databank, "sample": a.sample,
                    "feed": feeds, "timeframe": a.timeframe, "input": str(packed.resolve()),
                    "draws": cfg["nulls"]["draws"], "rungs": cfg["nulls"]["rungs"],
                    "seed": cfg["nulls"]["seed"], "overrides": a.set},
                   " ".join(["python3 -m studies.readings.monkey.report", "--project", a.project,
                             "--databank", a.databank, *(["--feed", a.feed] if a.feed else []),
                             "--timeframe", a.timeframe, "--sample", a.sample]),
                   {"nulls.csv": len(got["panel"])})
    print(f"\n{len(got['panel'])} estrategias x mercado ({len(feeds)} mercados) -> {out}")


if __name__ == "__main__":
    main()
