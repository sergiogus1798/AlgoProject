"""THE COMMAND: build (or report the cache of) one pool's universe, in Spanish for the owner."""

import argparse
import resource
import time
from pathlib import Path

import pandas as pd

from .equity import matrix, universe
from .inputs import config
from .pairs import table
from portfolio.common.construct.search import admissible

FILTER_WORDS = {"overlap": "solape < 24 meses", "undefined": "coeficiente indefinido"}


def _reconcile_lines(reconcile: pd.DataFrame) -> list[str]:
    """One line per member: its reconciliation share and licence, from the reconcile.csv frame."""
    lines = []
    for identity, rows in reconcile.groupby("identity"):
        first = rows.iloc[0]
        segments = ", ".join(f"{r.segment} {r.exact:.0%}" for r in rows.itertuples())
        estado = "excluida" if first.excluded else "conservada"
        lines.append(f"  {identity[:12]}… [{estado}] daily-low {segments} · "
                     f"MAE {first.mae_exact:.0%} · MFE {first.mfe_exact:.0%}"
                     + (f" · motivo: {first.reason}" if first.excluded else ""))
    return lines


def summarise(pool_name: str, cfg: dict, out: Path) -> str:
    """The Spanish report the owner reads after a build, or after finding the cache already built.

    Args:
        pool_name: The pool built.
        cfg: The run's config (for its `relaxed` flag).
        out: The folder `universe.build()` returned.

    Returns:
        The printed text, for the test to check without re-parsing stdout.
    """
    data = universe.load(out)
    manifest = data["manifest"]
    kept, excluded = manifest["members"]["kept"], manifest["members"]["excluded"]
    lines = [f"Universo del pool '{pool_name}' ({manifest['pool']['hash'][:12]}…)"]
    if cfg["relaxed"]:
        lines.append(f"AJUSTADO: umbrales relajados {cfg['relaxed']}")
    lines.append(f"Miembros: {len(kept)} conservados, {len(excluded)} excluidos de {len(kept) + len(excluded)}")
    lines += _reconcile_lines(data["reconcile"])
    lines.append("Calendario: " + ", ".join(f"{k} {v[0][:10]}…{v[1][:10]}"
                                            for k, v in manifest["calendar"].items()))
    for symbol, days in manifest["borrowed"].items():
        borrowed = {k: v for k, v in days.items() if v}
        if borrowed:
            lines.append(f"  {symbol} toma prestados {borrowed} días de otro de sus propios tramos")
    if manifest["unconfirmed_clocks"]:
        lines.append(f"Relojes sin confirmar: {manifest['unconfirmed_clocks']}")
    lines.append(f"Carpeta: {out}")
    text = "\n".join(lines)
    print(text)
    return text


def screen(data: dict, cfg: dict, out: Path) -> dict:
    """The pairwise screen on the build slice: every measure, the admissible graph, printed.

    Args:
        data: What `universe.load` returned.
        cfg: The run's config.
        out: The universe folder; `pairs.parquet` is written there (the folder is keyed by the
            config fingerprint, so a threshold change never reuses it).

    Returns:
        `search.admissible`'s dict.
    """
    calendar = {k: (pd.Timestamp(v[0]), pd.Timestamp(v[1]))
                for k, v in data["manifest"]["calendar"].items()}
    daily = matrix.segment(data["daily"], calendar, "build")
    monthly = matrix.segment(data["monthly"], calendar, "build")
    pairs = table.table(daily, monthly, cfg)
    pairs.to_parquet(out / "pairs.parquet")
    got = admissible.admissible(pairs, list(daily.columns), cfg)
    print(f"Parejas (solo build): {got['n_admissible_pairs']} admisibles de {got['n_pairs']}; "
          f"{got['n_out']} de {got['n_in']} estrategias tienen al menos una pareja admisible")
    for name, n in sorted(got["counts"].items(), key=lambda kv: -kv[1]):
        print(f"  caen por {FILTER_WORDS.get(name, name)}: {n}")
    if got["n_without_rolling"]:
        print(f"  juzgadas sin ventana móvil (menos de 60 meses compartidos): {got['n_without_rolling']}")
    calm, stress = got["effective_n"]["calm"], got["effective_n"]["stress"]
    print(f"N efectivo: calma {calm['participation']:.1f} / {calm['average']:.1f}, "
          f"estrés {stress['participation']:.1f} / {stress['average']:.1f} (autovalores / media de ρ)")
    return got


def main() -> None:
    """Build the pool's universe (or reuse its cache), print the owner's summary and the pair screen."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool", required=True)
    parser.add_argument("--set", dest="overrides", action="append", default=[])
    args = parser.parse_args()

    cfg = config.load(args.overrides)
    start = time.perf_counter()
    out = universe.build(args.pool, cfg)
    wall = time.perf_counter() - start
    peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

    summarise(args.pool, cfg, out)
    data = universe.load(out)
    if len(data["daily"].columns) > 1:
        screen(data, cfg, out)
    print(f"Tiempo: {wall:.2f} s · RAM pico: {peak_mb:.0f} MB")


if __name__ == "__main__":
    main()
