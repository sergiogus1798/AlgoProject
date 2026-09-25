#!/usr/bin/env python3
"""The study contract refuses what the window cannot draw, and every kind renders."""

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.study import blocks, config, result  # noqa: E402
from core.study.render import page  # noqa: E402


def every_kind() -> list[dict]:
    """One block of each of the eight kinds, built the way a module builds them."""
    rng = np.random.default_rng(0)
    return [
        blocks.distribution("d", "USD", rng.normal(0, 1, 10_000), 2.5, "n", p=0.01),
        blocks.cone("c", "USD", list(range(30)), rng.normal(0, 1, (500, 30)).cumsum(1),
                    list(np.linspace(0, 3, 30))),
        {"kind": "grid", "title": "g", "rows": ["a"], "cols": ["1", "2"],
         "values": [[0.1, None]], "scale": "diverging", "levels": None, "labels": None},
        {"kind": "scatter", "title": "s", "x_label": "x", "y_label": "y",
         "points": [{"x": 0.0, "y": 1.0, "label": "p", "group": "g"},
                    {"x": 1.0, "y": 0.0, "label": "q", "group": "g"}],
         "quadrants": True, "fit": None},
        {"kind": "bars", "title": "b", "unit": "", "reference": 0.0,
         "items": [{"label": "x", "value": 1.0, "error": None, "state": "pass"}]},
        {"kind": "lines", "title": "l", "unit": "", "x": [0, 1],
         "series": [{"label": "r", "values": [0.0, 1.0], "role": "real"}]},
        blocks.table("t", pd.DataFrame({"a": ["x"], "b": [np.nan]})),
        blocks.verdict("KEEP", "pass", "m"),
    ]


def main() -> None:
    """Build, validate, serialise and draw; then check what must be refused is refused."""
    got = every_kind()
    d = got[0]
    assert sum(d["counts"]) == 10_000 and len(d["bins"]) == 61, "histogram lost draws"
    assert abs(d["percentiles"]["50"]) < 0.05, "median of N(0,1) far from 0"
    assert len(got[1]["bands"]["50"]) == 30, "cone kept runs instead of percentiles"
    r = result.envelope("test", "S", None, {"k": 1}, time.time(),
                        [result.tab("t", "T", got)], verdict=got[-1])
    assert json.loads(json.dumps(r)) == r, "result does not survive JSON"
    html = page.page(r, "T")
    assert html.count("<svg") == 6, "a drawing kind did not draw"

    for bad in ({"kind": "pie"}, {**got[4], "items": [{**got[4]["items"][0], "state": "OK"}]},
                {k: v for k, v in got[2].items() if k != "scale"}):
        try:
            blocks.validate({"tabs": [{"name": "t", "blocks": [bad]}]})
        except ValueError:
            continue
        raise AssertionError(f"accepted {bad.get('kind')}")

    cfg = {"s": {"n": 1, "f": 0.5, "x": None}, "top": 7}
    config.apply(cfg, ["s.n=3", "s.f=2", "s.x=[1, 2]", "top=9"])
    assert cfg == {"s": {"n": 3, "f": 2.0, "x": [1, 2]}, "top": 9}, cfg
    try:
        config.apply(cfg, ["s.n=2e4"])
    except ValueError:
        print("ok")
        return
    raise AssertionError("a string replaced an int")


if __name__ == "__main__":
    main()
