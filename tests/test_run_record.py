#!/usr/bin/env python3
"""Known-answer test for OPEN.md #80: crossTF and structure must read an old run's own record
(blocks.json, ran.json) rather than today's assets/_build.yaml, and fall back only when it is
missing."""

import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.readings.structure import inputs as structure_inputs
from studies.transfer.crossTF import inputs as crosstf_inputs

TODAY_DOCTRINE = {"crosstf": {"timeframes": {"H1": ["H4", "D1"]}},
                  "wfc": {"tasks": [{"databank": "WFC_Build", "segment": "build"},
                                   {"databank": "WFC_OOS1", "segment": "oos1"}]}}


def main() -> None:
    """Fail loudly if either reader prefers today's config over the run's own file."""
    failures = []

    with tempfile.TemporaryDirectory() as tmp:
        batch = Path(tmp)

        # crossTF: blocks.json says the run actually used M30/H4 — today's doctrine (H1
        # base, H4/D1) must never override it.
        (batch / "blocks.json").write_text(
            json.dumps({"blocks": ["M30", "H4"]}), encoding="utf-8")
        scaling = pd.DataFrame({"source_tf": ["H1", "H1"]})
        with mock.patch("studies.transfer.crossTF.inputs.doctrine", return_value=TODAY_DOCTRINE):
            got = crosstf_inputs.blocks(scaling, None, batch)
        if got != ["M30", "H4"]:
            failures.append(f"blocks() con blocks.json dio {got}, se esperaba el del archivo")

        # No blocks.json: the doctrine is the only thing left, and it must still answer.
        empty = Path(tmp) / "no_file"
        empty.mkdir()
        with mock.patch("studies.transfer.crossTF.inputs.doctrine", return_value=TODAY_DOCTRINE):
            got = crosstf_inputs.blocks(scaling, None, empty)
        if got != ["H1", "H4", "D1"]:
            failures.append(f"blocks() sin archivo dio {got}, se esperaba la doctrina de hoy")

        # An explicit --set run.blocks= still wins over the file.
        with mock.patch("studies.transfer.crossTF.inputs.doctrine", return_value=TODAY_DOCTRINE):
            got = crosstf_inputs.blocks(scaling, ["H1", "H2"], batch)
        if got != ["H1", "H2"]:
            failures.append("blocks() ignoro un run.blocks explicito")

        # structure: ran.json says WFC_Build actually ran under oos1 (renamed since) — today's
        # wfc.tasks must never relabel it.
        (batch / "ran.json").write_text(json.dumps(
            {"legs": [{"databank": "WFC_Build", "segment": "oos1"}]}), encoding="utf-8")
        with mock.patch("studies.readings.structure.inputs.assetdata.doctrine",
                        return_value=TODAY_DOCTRINE):
            got = structure_inputs.segments(batch)
        if got != {"WFC_Build": "oos1"}:
            failures.append(f"segments() con ran.json dio {got}, se esperaba el del archivo")

        with mock.patch("studies.readings.structure.inputs.assetdata.doctrine",
                        return_value=TODAY_DOCTRINE):
            got = structure_inputs.segments(empty)
        if got != {"WFC_Build": "build", "WFC_OOS1": "oos1"}:
            failures.append(f"segments() sin archivo dio {got}, se esperaba la doctrina de hoy")

    print("\n".join(failures) or
          "ok: blocks.json y ran.json mandan sobre un run ya hecho; sin ellos, la doctrina de "
          "hoy sigue respondiendo; un run.blocks explicito sigue ganando a todos")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
