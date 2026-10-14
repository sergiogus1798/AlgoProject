#!/usr/bin/env python3
"""Known-answer test for `sqx.inspect.instruments`: an instrument SQX wrote with an empty or
a missing `commissions` attribute reads as "no commission declared" instead of crashing the
whole listing (OPEN.md #103). The project is built here, in a temp dir — no install is read."""

import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.inspect.instruments import commission, instruments  # noqa: E402

METHOD = (
    "&lt;Method use=&quot;{use}&quot; type=&quot;SizeBased&quot;&gt;&lt;Params&gt;"
    "&lt;Param key=&quot;Commission&quot;&gt;8&lt;/Param&gt;&lt;/Params&gt;&lt;/Method&gt;"
)
TASK = """<Task><Symbol name="PAID_M1" source="x">
  <InstrumentInfo instrument="PAID" defaultSpread="2.0" commissions="{paid}" swap="" />
</Symbol><Symbol name="EMPTY_M1" source="x">
  <InstrumentInfo instrument="EMPTY" defaultSpread="1.0" commissions="" swap="" />
</Symbol><Symbol name="NONE_M1" source="x">
  <InstrumentInfo instrument="NONE" defaultSpread="3.0" />
</Symbol></Task>"""


def test_commission() -> None:
    """In use, switched off, empty and blank: only the first names a method."""
    assert commission(METHOD.format(use="true")) == "SizeBased 8"
    assert commission(METHOD.format(use="false")) == ""
    assert commission("") == "" and commission("  ") == ""


def test_instruments() -> None:
    """One project carrying the three shapes lists all three instruments."""
    with tempfile.TemporaryDirectory() as tmp:
        built = Path(tmp) / "fixture.zip"
        with zipfile.ZipFile(built, "w") as z:
            z.writestr("config.xml", "<Project/>")
            z.writestr("Build-Task1.xml", TASK.format(paid=METHOD.format(use="true")))
        got = instruments(built)
    assert {k: v["commission"] for k, v in got.items()} == {
        "PAID_M1": "SizeBased 8",
        "EMPTY_M1": "",
        "NONE_M1": "",
    }, got
    assert (
        got["EMPTY_M1"]["defaultSpread"] == "1.0" and got["NONE_M1"]["swap"] is False
    ), got


if __name__ == "__main__":
    for test in (test_commission, test_instruments):
        test()
    print("ok: comisión vacía o ausente = sin comisión declarada")
