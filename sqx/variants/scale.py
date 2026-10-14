"""Rescale one strategy's bar-unit parameters to another timeframe, as a sibling .sqx.

Owner's rule, 2026-10-07 (it replaces «periods and bar-count exits, nothing else»): periods,
bar-count exits, and the coefficients that multiply a per-bar measure — those by the measured
ATR ratio. Nothing else."""

import argparse
import shutil
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from core import sqxfile
from core.assetdata import doctrine, symbols
from core.datapaths import crosstf_dir
from core.paths import ROOT
from sqx.variants import lengths, ranges
from sqx.variants.build import rewrite
from typing import Any

CONFIG = ROOT / "sqx" / "variants" / "config.yaml"

# A timeframe is only ever a number of minutes here, which is what makes a ratio meaningful.
MINUTES = {"M1": 1, "M5": 5, "M10": 10, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "H12": 720,
           "D1": 1440}


def knobs() -> dict[str, Any]:
    """The cross-timeframe section of the factory's config, with the custom-block table.

    Returns:
        Keys `scale` (the name patterns, a fallback), `floor`, `shape`, `atr_period`, `table`
        (`lengths.table`) and `measures` (`ranges.table`).
    """
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))["crosstf"] | {
        "table": lengths.table(), "measures": ranges.table()}


def ratio(source: str, target: str) -> float:
    """How many source bars fit in one target bar.

    Args:
        source, target: Timeframe codes, keys of `MINUTES`.

    Returns:
        Greater than 1 going up (H1 to H4 is 4.0), less than 1 going down.
    """
    return MINUTES[target] / MINUTES[source]


def rescaled(values: dict[str, str], types: dict[str, str], names: list[str],
             factor: float, floor: int) -> dict[str, dict]:
    """What each bar-unit parameter becomes on the target timeframe.

    Rounding is not cosmetic: a period of 9 divided by 4 is 2.25, and writing 2 is a 11 %
    move on top of the timeframe change. `shift` records that so the study can tell the
    two apart, and `clamped` marks a period the floor rescued from being unbuildable.
    Halves round up, because `round` in Python rounds 2.5 to 2 and a period is not a
    quantity anyone expects banker's rounding on.

    Args:
        values: Variable to stored value, from `rewrite.values`.
        types: Variable to `int`, `double` or `boolean`, from `rewrite.declared`.
        names: The lengths `lengths.split` returned.
        factor: Output of `ratio`.
        floor: Smallest period the builder will accept, in bars.

    Returns:
        Per parameter: `original`, `exact`, `written`, `shift` and `clamped`.
    """
    out = {}
    for name in names:
        original = float(values[name])
        exact = original / factor
        written = max(int(exact + 0.5), floor) if types[name] == "int" else exact
        out[name] = {"original": original, "exact": exact, "written": float(written),
                     "shift": abs(written - exact) / exact if exact else 0.0,
                     "clamped": types[name] == "int" and int(exact + 0.5) < floor}
    return out


def atr_ratio(symbol: str, source: str, target: str, cfg: dict) -> float | None:
    """c for one batch and target: the market's ATR ratio at the config's reference period.

    Args:
        symbol: The asset the mothers trade, or "" when nobody could say.
        source, target: The mothers' timeframe and the siblings'.
        cfg: Output of `knobs`.

    Returns:
        `ranges.measured` with the period rescaled as a sibling's is, or None for a symbol
        `assets/` does not declare — its per-bar coefficients then stay and are flagged.
    """
    if symbol not in symbols():
        return None
    period = cfg["atr_period"]
    scaled = rescaled({"p": str(period)}, {"p": "int"}, ["p"], ratio(source, target),
                      cfg["floor"])["p"]["written"]
    return ranges.measured(symbol, source, target, period, int(scaled))


def sibling(mother: Path, out: Path, source: str, target: str, cfg: dict,
            index: int, c: float | None = None) -> dict[str, Any]:
    """Write one timeframe-scaled copy of a mother strategy.

    Args:
        mother: The `.sqx` to read. Never modified.
        out: Folder the sibling is written into.
        source: The timeframe the mother was built on.
        target: The timeframe its periods are being moved to.
        cfg: Output of `knobs`.
        index: Position in the batch, so the stamped identifier stays unique.
        c: Output of `atr_ratio` for this target; None leaves the per-bar coefficients
            alone and flags them.

    Returns:
        One manifest row: what was written, where, every parameter that moved,
        `n_coef_scaled` and `atr_ratio` (the coefficients divided by c, and c), and
        `unverified` — the lengths and coefficients nobody could rule on, left unscaled.
    """
    parts = rewrite.members(mother)
    portfolio = parts[rewrite.PORTFOLIO].decode("utf-8")
    types, values = rewrite.declared(portfolio), rewrite.values(portfolio)

    factor = ratio(source, target)
    bars, loose = lengths.split(portfolio, cfg["scale"], cfg["table"])
    measure = ranges.measures(portfolio, cfg["measures"])
    # What the measures table rules is not a length, whatever SQX typed it (a StdDevMult).
    moved = rescaled(values, types, [n for n in bars if n not in measure], factor, cfg["floor"])
    # A per-bar coefficient needs c and a double to hold k / c; without either it stays, flagged.
    coefs = {n: float(values[n]) / c for n, m in measure.items()
             if m == ranges.BAR and c and types[n] == "double"}
    loose += [n for n, m in measure.items()
              if n not in coefs and m in (ranges.BAR, ranges.UNVERIFIED)]
    portfolio, literal, periods = ranges.stops(
        portfolio, c, lambda p: rescaled({"p": str(p)}, {"p": "int"}, ["p"], factor,
                                         cfg["floor"])["p"])
    loose += [ranges.LITERAL] if literal and not c else []
    parts = {**parts, rewrite.PORTFOLIO: portfolio.encode("utf-8")}
    shifts = [*moved.values(), *periods]
    name = f"{mother.stem}_Scaled{target}"
    variant_id = f"CTF{index:03d}{target}"
    path = out / f"{name}.sqx"
    rewrite.save(path, rewrite.variant(parts, variant_id, name,
                                       {k: v["written"] for k, v in moved.items()} | coefs),
                 cfg["shape"])

    row = {"variant_id": variant_id, "mother": mother.stem, "name": name,
           "source_tf": source, "target_tf": target, "ratio": factor,
           "n_scaled": len(moved) + len(periods),
           "n_coef_scaled": len(coefs) + (literal if c else 0),
           "atr_ratio": c if c else float("nan"),
           "max_rounding_shift": max((v["shift"] for v in shifts), default=0.0),
           "clamped": any(v["clamped"] for v in shifts),
           "unverified": ",".join(loose), "path": str(path)}
    row.update({f"param_{k}": v["written"] for k, v in moved.items()})
    row.update({f"was_{k}": v["original"] for k, v in moved.items()})
    row.update({f"param_{k}": v for k, v in coefs.items()})
    row.update({f"was_{k}": float(values[k]) for k in coefs})
    return row


def unmatched(mother: Path, cfg: dict) -> list[str]:
    """Integer parameters left untouched, so the rules can be reviewed against real files.

    Args:
        mother: A `.sqx`.
        cfg: Output of `knobs`.

    Returns:
        Names of int variables not rescaled, without SQX's UUID-named internals and without
        what SQX itself types a shift.
    """
    portfolio = rewrite.members(mother)[rewrite.PORTFOLIO].decode("utf-8")
    types, kind = rewrite.declared(portfolio), lengths.kinds(portfolio)
    claimed = set(lengths.split(portfolio, cfg["scale"], cfg["table"])[0])
    return [n for n, t in types.items() if t == "int" and n not in claimed
            and not n[0].isdigit() and kind[n] != lengths.SHIFT]


def fabricate(mothers: list[Path], out: Path, source: str, targets: list[str],
              symbol: str | None = None) -> pd.DataFrame:
    """Write every mother's siblings, the mothers beside them, and the manifest.

    Args:
        mothers: The `.sqx` built on `source`.
        out: The batch folder (`core.datapaths.crosstf_dir`); `sqx/` under it is the load.
        source: The mothers' timeframe.
        targets: Timeframes to move their periods to — slower (H4) or faster (M30) alike:
            a faster target multiplies the periods, which never clamps and never rounds.
        symbol: The asset whose bars give c; default, the one the first mother was tested on.

    Returns:
        The manifest, also written as `scaling.parquet` one level above the load.
    """
    cfg = knobs()
    # The .sqx go in a folder of their own: SQX loads every file of the folder it is given,
    # and logged "No plugin loader was able to recognize" for scaling.parquet beside them.
    load = out / "sqx"
    load.mkdir(parents=True, exist_ok=True)
    symbol = symbol or (sqxfile.symbol(mothers[0])[0] if mothers else "")
    c = {t: atr_ratio(symbol, source, t, cfg) for t in targets}
    rows = [sibling(m, load, source, t, cfg, i, c[t])
            for t in targets for i, m in enumerate(mothers)]
    frame = pd.DataFrame(rows)
    frame.to_parquet(out / "scaling.parquet", index=False)
    # The mothers ride along verbatim, because the folder IS the databank load: the study
    # needs the baseline and the control cells, and those are the mothers' own rows. They
    # are copied rather than rewritten -- a mother stripped of its fingerprint or its
    # results is no longer the thing the siblings are being compared against.
    for m in mothers:
        shutil.copy2(m, load / m.name)
    return frame


def main() -> None:
    """Rescale a folder of mothers to each target timeframe and write the manifest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mothers", required=True, type=Path,
                        help="Folder of .sqx built on --source")
    parser.add_argument("--project", required=True,
                        help="project the mothers came from; names the output tree")
    parser.add_argument("--out", type=Path,
                        help="override the declared location under the data root")
    parser.add_argument("--source", default="H1", choices=sorted(MINUTES))
    parser.add_argument("--targets", nargs="+", choices=sorted(MINUTES),
                        help="default: the doctrine's list for --source (crosstf.timeframes)")
    parser.add_argument("--symbol", help="asset whose bars give the ATR ratio; default: the "
                                         "one the first mother was tested on")
    args = parser.parse_args()
    args.targets = args.targets or doctrine()["crosstf"]["timeframes"][args.source]

    out = args.out or crosstf_dir(args.project, date.today().isoformat())
    mothers = sorted(args.mothers.glob("*.sqx"))
    frame = fabricate(mothers, out, args.source, args.targets, args.symbol)
    print(f"-> {out / 'sqx'}  ({len(mothers)} madres copiadas con ellas; esta carpeta es la carga)")
    print(f"{len(mothers)} mothers x {len(args.targets)} targets -> {len(frame)} siblings")
    print(frame[["name", "ratio", "n_scaled", "n_coef_scaled", "atr_ratio",
                 "max_rounding_shift", "clamped", "unverified"]]
          .to_string(index=False))
    cfg = knobs()
    loose = sorted({n for m in mothers for n in unmatched(m, cfg)})
    if loose:
        print(f"\nint parameters left untouched ({len(loose)}) -- review lengths.yaml:")
        print("  " + ", ".join(loose))


if __name__ == "__main__":
    main()
