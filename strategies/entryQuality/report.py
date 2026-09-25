#!/usr/bin/env python3
"""The panel: whether the entry itself carries information, and what arriving late costs."""

import argparse
from pathlib import Path

import numpy as np

from core.barstore import read as read_bars
from nulls import calibrate
from strategies.entryQuality import delay, eratio, excursion, inputs, verdict


def read(packed: Path, strategy: str, cfg: dict) -> dict:
    """Every measurement for one strategy, with nothing judged and nothing printed.

    Args:
        packed: The `trades.parquet` an export wrote.
        strategy: Its name exactly as the export spells it.
        cfg: What `inputs.config` returned.

    Returns:
        The e-ratio curve and its band, the two delay tables, and the counts behind them.
    """
    run, e, d = cfg["run"], cfg["eratio"], cfg["delay"]
    frame = read_bars(run["feed"], run["timeframe"])
    found = inputs.located(packed, strategy, run, frame)
    keep = inputs.usable(found, e["horizon"], len(frame))

    price = found["trades"]["Open price"].to_numpy(np.float64)
    walk = excursion.paths(frame, found["entry"][keep], found["side"][keep],
                           price[keep], e["horizon"])
    scale = calibrate.atr(frame, run["atr"])
    normal = excursion.normalised(walk, found["atr"][keep])
    real = eratio.curve(normal)
    bands = eratio.band(frame, found, keep, scale, e)

    opens = frame["Open"].to_numpy()
    on_tf = delay.cost(delay.given_up(opens, found["entry"], found["side"], d["bars"]),
                       found["size"], found["point_value"],
                       found["trades"]["Profit/Loss"].to_numpy(np.float64),
                       found["charged"], d["bars"])

    minute = read_bars(run["feed"], "M1")
    at_m1 = minute.index.searchsorted(found["trades"]["Open time"].to_numpy())
    on_m1 = delay.cost(delay.given_up(minute["Open"].to_numpy(), at_m1, found["side"],
                                      d["minutes"]),
                       found["size"], found["point_value"],
                       found["trades"]["Profit/Loss"].to_numpy(np.float64),
                       found["charged"], d["minutes"])

    hold = (found["trades"]["Close time"] - found["trades"]["Open time"])
    return {"found": found, "keep": keep, "real": real, "bands": bands,
            "walk": normal, "on_tf": on_tf, "on_m1": on_m1,
            "peak": int(np.argmax(real)) + 1, "hold": hold.median()}


def sides(found: dict, normal: dict, keep: np.ndarray, marks: list[int]) -> str:
    """The e-ratio split by direction, which can hide a dead half.

    Args:
        found: What `inputs.located` returned.
        normal: What `excursion.normalised` returned.
        keep: The usable mask.
        marks: Horizons to print.

    Returns:
        One line per direction. A strategy whose longs carry everything is a different
        object from one whose two halves work, and the pooled curve shows neither.
    """
    lines = []
    for name, want in (("largos", 1.0), ("cortos", -1.0)):
        mask = found["side"][keep] == want
        if not mask.any():
            continue
        part = eratio.curve({k: v[mask] for k, v in normal.items()})
        shown = " · ".join(f"k={k} {part[k - 1]:.2f}" for k in marks)
        lines.append(f"{name} ({int(mask.sum())}): {shown}")
    return "\n".join(lines)


def main() -> None:
    """Read one strategy's entries against the bars and print what they were worth."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--export", required=True, type=Path, help="a trades.parquet")
    ap.add_argument("--strategy", required=True, help="its name as the export spells it")
    ap.add_argument("--set", dest="overrides", action="append", default=[])
    a = ap.parse_args()

    cfg = inputs.config(a.overrides)
    found = read(a.export, a.strategy, cfg)
    run, e = cfg["run"], cfg["eratio"]
    kept, total = int(found["keep"].sum()), found["keep"].size

    print(f"{a.strategy} · muestra {run['sample']} · {run['feed']} {run['timeframe']} · "
          f"{kept} de {total} operaciones con camino completo")

    print("\n-- 3 · calidad de la entrada (MFE/MAE contra entradas al azar)")
    print(eratio.table(found["real"], found["bands"], e["marks"]).round(3).to_string())
    print(sides(found["found"], found["walk"], found["keep"], e["marks"]))
    print(f"máximo de e(k) en k={found['peak']} · duración mediana real "
          f"{found['hold']}")
    call = verdict.signal(found["real"], found["bands"])
    print(f"-> {call}: {verdict.MEANS[call]}")

    print(f"\n-- 4 · lo que cuesta llegar tarde (tier 1, salidas sin mover)")
    print(f"en barras de {run['timeframe']}:")
    print(found["on_tf"].round(3).to_string())
    print("en minutos:")
    print(found["on_m1"].round(3).to_string())
    call = verdict.latency(found["on_tf"], cfg["verdict"]["dcr_high"])
    print(f"-> {call}: {verdict.MEANS[call]}")
    print("\nTier 1 supone que las salidas no se mueven. Con stop o target eso es falso, "
          "y ahí manda el simulador de replay: docs/encargos/16-replay-de-operaciones.md")


if __name__ == "__main__":
    main()
