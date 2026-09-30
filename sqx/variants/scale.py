"""Rescale one strategy's bar-unit parameters to another timeframe, as a sibling .sqx."""

import argparse
import re
import shutil
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from core.assetdata import doctrine
from core.datapaths import crosstf_dir
from core.paths import ROOT
from sqx.variants.build import rewrite

CONFIG = ROOT / "sqx" / "variants" / "config.yaml"

# A timeframe is only ever a number of minutes here, which is what makes a ratio meaningful.
MINUTES = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "H12": 720, "D1": 1440}


def knobs() -> dict:
    """The cross-timeframe section of the factory's config.

    Returns:
        Keys `scale` (regex whitelist), `floor` and `shape`.
    """
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))["crosstf"]


def ratio(source: str, target: str) -> float:
    """How many source bars fit in one target bar.

    Args:
        source, target: Timeframe codes, keys of `MINUTES`.

    Returns:
        Greater than 1 going up (H1 to H4 is 4.0), less than 1 going down.
    """
    return MINUTES[target] / MINUTES[source]


def in_bars(names: list[str], patterns: list[str]) -> list[str]:
    """Which parameters are measured in bars, and so move with the timeframe.

    This is a positive whitelist, never a classification: anything the patterns do not
    name is written through untouched. Coefficients, deviations, oscillator levels,
    shifts and categorical selectors are all left alone by that rule, deliberately.

    Args:
        names: Every variable the strategy declares.
        patterns: Regexes from `config.yaml`, matched with `search`.

    Returns:
        The subset to rescale, in declaration order.
    """
    return [n for n in names if any(re.search(p, n) for p in patterns)]


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
        names: The subset returned by `in_bars`.
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


def sibling(mother: Path, out: Path, source: str, target: str, cfg: dict,
            index: int) -> dict:
    """Write one timeframe-scaled copy of a mother strategy.

    Args:
        mother: The `.sqx` to read. Never modified.
        out: Folder the sibling is written into.
        source: The timeframe the mother was built on.
        target: The timeframe its periods are being moved to.
        cfg: Output of `knobs`.
        index: Position in the batch, so the stamped identifier stays unique.

    Returns:
        One manifest row: what was written, where, and every parameter that moved.
    """
    parts = rewrite.members(mother)
    portfolio = parts[rewrite.PORTFOLIO].decode("utf-8")
    types, values = rewrite.declared(portfolio), rewrite.values(portfolio)

    factor = ratio(source, target)
    moved = rescaled(values, types, in_bars(list(types), cfg["scale"]), factor,
                     cfg["floor"])
    name = f"{mother.stem}_Scaled{target}"
    variant_id = f"CTF{index:03d}{target}"
    path = out / f"{name}.sqx"
    rewrite.save(path, rewrite.variant(parts, variant_id, name,
                                       {k: v["written"] for k, v in moved.items()}),
                 cfg["shape"])

    row = {"variant_id": variant_id, "mother": mother.stem, "name": name,
           "source_tf": source, "target_tf": target, "ratio": factor,
           "n_scaled": len(moved),
           "max_rounding_shift": max((v["shift"] for v in moved.values()), default=0.0),
           "clamped": any(v["clamped"] for v in moved.values()), "path": str(path)}
    row.update({f"param_{k}": v["written"] for k, v in moved.items()})
    row.update({f"was_{k}": v["original"] for k, v in moved.items()})
    return row


def unmatched(mother: Path, cfg: dict) -> list[str]:
    """Integer parameters the whitelist did not claim, so the patterns can be reviewed.

    Args:
        mother: A `.sqx`.
        cfg: Output of `knobs`.

    Returns:
        Names of int variables left untouched, excluding SQX's own UUID-named internals.
    """
    portfolio = rewrite.members(mother)[rewrite.PORTFOLIO].decode("utf-8")
    types = rewrite.declared(portfolio)
    claimed = set(in_bars(list(types), cfg["scale"]))
    return [n for n, t in types.items()
            if t == "int" and n not in claimed and not n[0].isdigit()]


def fabricate(mothers: list[Path], out: Path, source: str, targets: list[str]) -> pd.DataFrame:
    """Write every mother's siblings, the mothers beside them, and the manifest.

    Args:
        mothers: The `.sqx` built on `source`.
        out: The batch folder (`core.datapaths.crosstf_dir`); `sqx/` under it is the load.
        source: The mothers' timeframe.
        targets: Timeframes to move their periods to — slower (H4) or faster (M30) alike:
            a faster target multiplies the periods, which never clamps and never rounds.

    Returns:
        The manifest, also written as `scaling.parquet` one level above the load.
    """
    cfg = knobs()
    # The .sqx go in a folder of their own: SQX loads every file of the folder it is given,
    # and logged "No plugin loader was able to recognize" for scaling.parquet beside them.
    load = out / "sqx"
    load.mkdir(parents=True, exist_ok=True)
    rows = [sibling(m, load, source, t, cfg, i)
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
    args = parser.parse_args()
    args.targets = args.targets or doctrine()["crosstf"]["timeframes"][args.source]

    out = args.out or crosstf_dir(args.project, date.today().isoformat())
    mothers = sorted(args.mothers.glob("*.sqx"))
    frame = fabricate(mothers, out, args.source, args.targets)
    print(f"-> {out / 'sqx'}  ({len(mothers)} madres copiadas con ellas; esta carpeta es la carga)")
    print(f"{len(mothers)} mothers x {len(args.targets)} targets -> {len(frame)} siblings")
    print(frame[["name", "ratio", "n_scaled", "max_rounding_shift", "clamped"]]
          .to_string(index=False))
    cfg = knobs()
    loose = sorted({n for m in mothers for n in unmatched(m, cfg)})
    if loose:
        print(f"\nint parameters left untouched ({len(loose)}) -- review the whitelist:")
        print("  " + ", ".join(loose))


if __name__ == "__main__":
    main()
