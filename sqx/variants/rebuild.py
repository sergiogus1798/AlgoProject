"""Write a step-12 scaled sister again from the stored mother and the parameters the store kept."""

import argparse
import io
import math
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import pandas as pd

from core import sqxfile
from core.store.extra import FABRICATED
from core.store.write import SQX, folder, manifest
from sqx.variants import scale


def kept(identity: str, member: str, prefix: str) -> pd.DataFrame:
    """One table out of the stored strategy's zips whose name starts with `prefix`, all days joined."""
    frames = []
    for path in sorted(folder(identity).glob(f"{prefix}*.zip")):
        with zipfile.ZipFile(path) as z:
            if member in z.namelist():
                data = io.BytesIO(z.read(member))
                frames.append(pd.read_parquet(data) if member.endswith(".parquet") else pd.read_csv(data))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def sister(identity: str, target: str, out: Path) -> tuple[Path, list[str]]:
    """Scale the stored mother to `target` again and compare with what step 12 wrote then.

    Args:
        identity: The stored mother.
        target: The sister's timeframe, e.g. `H1`.
        out: Folder to write `<mother>_Scaled<target>.sqx` into.

    Returns:
        (the file, what differs from the stored record). The ATR ratio and the batch index
        are the stored ones, not recomputed: today's bars and today's batch are not that
        day's. Differences are a parameter the scaler writes differently now, or a file whose
        identity is not that of the one fabricated then — the scaling rules changed since,
        and the stored row's `param_*` say what the sister was. The identity SQX gave the
        sister when it retested it is another one, and is not what is compared.
    """
    name = manifest(identity)["origin"]["strategy"]
    rows = kept(identity, "scaling.parquet", "hermanas.")
    rows = rows[rows["target_tf"] == target] if len(rows) else rows
    if not len(rows):
        raise SystemExit(f"{name}: el almacén no guarda una hermana en {target}")
    row = rows.iloc[-1]
    c = None if math.isnan(row["atr_ratio"]) else float(row["atr_ratio"])
    with tempfile.TemporaryDirectory() as tmp:
        mother = Path(tmp) / f"{name}.sqx"      # the scaler names the sister after the file
        shutil.copy2(folder(identity) / SQX, mother)
        out.mkdir(parents=True, exist_ok=True)
        got = scale.sibling(mother, out, row["source_tf"], target, scale.knobs(),
                            int(row["variant_id"][3:6]), c)
    was = {k: v for k, v in row.items() if k.startswith("param_") and pd.notna(v)}
    bad = [f"{k[6:]}: guardado {was[k]}, ahora {got.get(k)}" for k in sorted(was)
           if got.get(k) is None or float(got[k]) != float(was[k])]
    path = Path(got["path"])
    if row.get(FABRICATED) and sqxfile.identity(path) != row[FABRICATED]:
        bad.append(f"la huella {sqxfile.identity(path)[:12]} no es la del archivo de entonces "
                   f"({row[FABRICATED][:12]})")
    return path, bad


def main() -> None:
    """Rebuild one sister, or every one the store keeps of a mother."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("identity", help="huella de la madre guardada (python3 -m core.store list)")
    ap.add_argument("timeframes", nargs="*", help="M15 H1 H4…; sin ninguno, todas las guardadas")
    ap.add_argument("--out", type=Path, required=True, help="carpeta donde escribir los .sqx")
    a = ap.parse_args()
    frames = a.timeframes or sorted(set(kept(a.identity, "scaling.parquet", "hermanas.")["target_tf"]))
    wrong = 0
    for target in frames:
        path, bad = sister(a.identity, target, a.out)
        print(f"{'DISTINTA' if bad else 'igual   '}  {path}")
        for line in bad:
            print(f"    {line}")
        wrong += bool(bad)
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
