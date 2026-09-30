#!/usr/bin/env python3
"""Cross TF (owner, 2026-09-30): every timeframe a task of its own, never a block of the
cross-check whose export cannot be split on one symbol — D1 on MetaTrader 4 — and the study
reads each task's export as that timeframe's block."""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.projects import crosstfsolo
from studies.transfer.crossTF import inputs

CONFIG = ('<Project><Tasks>\n'
          '  <Task type="Retest" name="Retest strategies 15" active="true" '
          'taskXMLFile="Retest-Task15.xml" title="CrossTF" />\n  </Tasks>\n<Databanks>\n'
          '    <Databank name="CrossTF" position="100" />\n  </Databanks></Project>')
TASK = ('<Task><Data><Setups><Setup dateFrom="2008.01.01" engine="MetaTrader5 (hedged)">'
        '<Chart symbol="USDJPY_DukasM1_the5ers" timeframe="H1" /></Setup></Setups></Data>'
        '<RetestOnAdditionalMarkets use="true"><Settings><Setups detailed="true">'
        '<Setup engine="MetaTrader5 (hedged)"><Chart symbol="USDJPY_DukasM1_the5ers" '
        'timeframe="H4" /></Setup></Setups></Settings></RetestOnAdditionalMarkets>'
        '<Condition use="true" /><Databanks retestSelected="false">'
        '<Databank label="Output databank" name="Output" value="CrossTF" />'
        '<Databank label="Input databank" name="Input" value="CrossTF_Input" /></Databanks></Task>')
SOLO = {"timeframe": "D1", "title": "CrossTF D1", "databank": "CrossTF_D1",
        "engine": "MetaTrader4"}


def test_d1_task_is_written_beside_crosstf() -> None:
    """A new task, its own databank declared, on D1 and MT4, with no cross-check and no live
    condition; written twice, it is rewritten in place, never duplicated."""
    members = {"config.xml": CONFIG.encode(), "Retest-Task15.xml": TASK.encode()}
    member = crosstfsolo.write(members, TASK, SOLO)
    assert member == crosstfsolo.write(members, TASK, SOLO) == "Retest-Task16.xml"
    config = members["config.xml"].decode()
    assert crosstfsolo.present(config) == ["CrossTF D1"]
    assert '<Databank name="CrossTF_D1"' in config
    task = members[member].decode()
    assert 'timeframe="H1"' not in task and 'timeframe="H4"' not in task
    assert 'engine="MetaTrader5' not in task and 'engine="MetaTrader4"' in task
    assert '<RetestOnAdditionalMarkets use="false"' in task and 'use="true"' not in task
    assert 'name="Output" value="CrossTF_D1"' in task
    assert 'name="Input" value="CrossTF_Input"' in task


def test_study_reads_one_databank_per_timeframe(tmp_path: Path) -> None:
    """CrossTF is block 0 whatever its rows said; CrossTF_M30, _H4, _D1 become 1, 2, 3."""
    batch = tmp_path / "batch"
    batch.mkdir()
    banks = ["CrossTF", "CrossTF_M30", "CrossTF_H4", "CrossTF_D1"]
    (batch / "blocks.json").write_text(json.dumps({"blocks": ["H1", "M30", "H4", "D1"],
                                                   "databanks": banks}))
    day = tmp_path / "raw" / "P" / "{}" / "2026-09-30"
    export = Path(str(day).format("CrossTF")) / "trades.parquet"
    for i, bank in enumerate(banks):
        folder = Path(str(day).format(bank))
        folder.mkdir(parents=True)
        pd.DataFrame({"strategy": ["A", f"A_Scaled{bank[-2:]}"], "Ticket": [1, 1],
                      "Profit/Loss": [float(i), 1.0]}).to_parquet(folder / "trades.parquet")
    got = inputs.gather(batch, export, pd.read_parquet(export))
    assert list(got["block"]) == [0, 0, 1, 1, 2, 2, 3, 3]
    assert list(got.loc[got["block"] == 3, "Profit/Loss"]) == [3.0, 1.0]

if __name__ == "__main__":
    import tempfile
    test_d1_task_is_written_beside_crosstf()
    with tempfile.TemporaryDirectory() as tmp:
        test_study_reads_one_databank_per_timeframe(Path(tmp))
    print("ok")
