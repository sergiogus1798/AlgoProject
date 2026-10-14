"""The study page's «Estrategia» dropdown: picking an entry announces that strategy's identity."""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication  # noqa: E402

from ui.desktop.studypage.picker import StrategyPicker  # noqa: E402

app = QApplication.instance() or QApplication([])
rows = [{"strategy": f"S {i}", "identity": f"id{i}"} for i in range(3)]
pick, got = StrategyPicker(), []
pick.picked.connect(lambda n, i: got.append((n, i)))
pick.bank = ("P", "Results")
pick.current = "S 0"
pick.take(
    "P", "Results", "Results", {"strategies": rows, "cells": {"id0": {"gate": {}}}}
)
# the study's result lives in another databank, under another identity, paired by name
pick.take(
    "P",
    "Results",
    "WFM",
    {
        "strategies": [{"strategy": "S 2", "identity": "other"}],
        "cells": {"other": {"wfm": {}}},
    },
)
pick.study = "gate"
pick.refill()
assert [r["strategy"] for r in pick.rows] == ["S 0"]
pick.study = "wfm"
pick.refill()
assert [r["strategy"] for r in pick.rows] == ["S 2"] and pick.rows[0][
    "identity"
] == "id2"
# a databank that drops the name's prefix but keeps the identity (MCR_All)
pick.take(
    "P",
    "Results",
    "MCR",
    {
        "strategies": [{"strategy": "1", "identity": "id1"}],
        "cells": {"id1": {"mcRetest": {}}},
    },
)
pick.study = "mcRetest"
pick.refill()
assert [r["strategy"] for r in pick.rows] == ["S 1"]
pick.study = ""
pick.refill()
assert len(pick.rows) == 3  # the Ficha: every strategy
pick.current = "S 0"
pick.choose("S 2")
assert got == [("S 2", "id2")], got
pick.choose("typed nonsense")
assert len(got) == 1
print("ok")
