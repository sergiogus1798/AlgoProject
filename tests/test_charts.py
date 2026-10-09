#!/usr/bin/env python3
"""The extra chart of a multi-timeframe template: inserted in all three places, once."""

import zipfile
from pathlib import Path

from sqx.projects import charts, stage
from sqx.projects.tasksettings import set_timeframe

CHART = '<Chart symbol="EURUSD_M1" timeframe="M30" spread="1.2" />'
TASK = f"""<Task>
  <StrategyType type="template" templateFile="{{tpl}}" />
  <WhatToBuild><RulesComplexity>
    <Chart name="Main chart" minConditions="1" maxConditions="1" />
  </RulesComplexity></WhatToBuild>
  <Datas>
    <data><id>0</id><timeFrame>0</timeFrame></data>
  </Datas>
  <Settings><Data><Setups>
    <Setup engine="MetaTrader5 (hedged)">
      {CHART}
      <Swap use="true" />
    </Setup>
  </Setups></Data>
  <CrossChecks><RetestOnAdditionalMarkets><Settings><Setups>
    <Setup engine="MetaTrader5 (hedged)">
      <Chart symbol="GBPUSD_M1" timeframe="M30" spread="1.4" />
    </Setup>
  </Setups></Settings></RetestOnAdditionalMarkets></CrossChecks>
  </Settings>
</Task>"""


def template(tmp: Path, streams: list[int]) -> Path:
    """A .sqx declaring one main chart plus one <data> per extra stream."""
    datas = "".join(f"<data><id>{i + 1}</id><timeFrame>{tf}</timeFrame></data>"
                    for i, tf in enumerate(streams))
    path = tmp / f"t{len(streams)}.sqx"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("strategy_Portfolio.xml",
                   "<StrategyFile><Strategy><Datas>"
                   "<data><id>0</id><timeFrame>0</timeFrame></data>"
                   f"{datas}</Datas></Strategy></StrategyFile>")
    return path


def test_single_chart_template_is_untouched(tmp_path: Path) -> None:
    """A one-chart template leaves the task exactly as it was."""
    text = TASK.format(tpl=template(tmp_path, []))
    assert charts.wanted(template(tmp_path, [])) == []
    assert charts.ensure(text, []) == (text, 0)
    assert charts.missing(text, []) == []


def test_every_setup_gets_the_extra_chart(tmp_path: Path) -> None:
    """All three insertions land, and the cross-check Setup is patched too."""
    text = TASK.format(tpl=template(tmp_path, [1440]))
    assert charts.missing(text, [1440]), "a 2-chart template on a 1-chart task must be refused"
    out, added = charts.ensure(text, [1440])
    assert added == 2, "both the main Setup and the cross-check Setup count"
    for setup in charts.SETUP.findall(out):
        assert len(charts.SETUP_CHART.findall(setup)) == 2
    # The inserted chart keeps its own Setup's symbol and spread, not the first one's.
    assert '<Chart symbol="GBPUSD_M1" timeframe="D1" spread="1.4" />' in out
    assert "<timeFrame>1440</timeFrame>" in out, "the task's own <Datas> stream"
    assert '<Chart name="D1 chart"' in out, "the list the builder indexes #Chart# against"
    assert charts.missing(out, [1440]) == []


def test_reconfiguring_does_not_pile_up_charts(tmp_path: Path) -> None:
    """A second pass flattens every chart onto the main timeframe; ensure must not add a third."""
    text, _ = charts.ensure(TASK.format(tpl=template(tmp_path, [1440])), [1440])
    flattened, _ = set_timeframe(text, "M30")
    again, _ = charts.ensure(flattened, [1440])
    for setup in charts.SETUP.findall(again):
        found = charts.SETUP_CHART.findall(setup)
        assert len(found) == 2, found
        assert [tf for _, tf, _ in found] == ["M30", "D1"]
    assert again.count('<Chart name="D1 chart"') == 1
    assert again.count("<timeFrame>1440</timeFrame>") == 1
    assert charts.missing(again, [1440]) == []


def test_a_stream_sqx_has_no_name_for_is_refused(tmp_path: Path) -> None:
    """A stream timeframe with no chart name in SQX is refused, never guessed."""
    text = TASK.format(tpl=template(tmp_path, [5]))
    try:
        charts.ensure(text, [5])
    except SystemExit as e:
        assert "TF_NAME" in str(e)
    else:
        raise AssertionError("a stream with no chart name must be refused, not guessed")


def test_the_silent_failure_is_reported(tmp_path: Path) -> None:
    """A task whose Setups are right but whose RulesComplexity is not: builds, reads wrong."""
    out, _ = charts.ensure(TASK.format(tpl=template(tmp_path, [1440])), [1440])
    without = out.replace('<Chart name="D1 chart" minConditions="1" maxConditions="1" />', "")
    assert any("#Chart#=1" in line for line in charts.missing(without, [1440]))


def test_stage_wires_the_task_it_activates(tmp_path: Path) -> None:
    """Every step activates its task through stage.just: a Setup rebuilt with one chart is mended."""
    build = TASK.format(tpl=template(tmp_path, [1440]))
    retest = f'<Task><Setups><Setup engine="x">{CHART}</Setup></Setups></Task>'
    config = ('<Project><Tasks><Task type="Build" name="Build strategies" active="true" '
              'taskXMLFile="Build-Task3.xml" title="CONSTRUCCION" /><Task type="Retest" '
              'name="Retest" active="false" taskXMLFile="Retest-Task1.xml" title="OOS" />'
              '</Tasks></Project>')
    cfx = tmp_path / "project.cfx"
    with zipfile.ZipFile(cfx, "w") as z:
        z.writestr("config.xml", config)
        z.writestr("Build-Task3.xml", build)
        z.writestr("Retest-Task1.xml", retest)
    assert stage.just(cfx, ["OOS"]) == [("CONSTRUCCION", False), ("OOS", True)]
    with zipfile.ZipFile(cfx) as z:
        assert charts.missing(z.read("Retest-Task1.xml").decode("utf-8"), [1440]) == []
        assert z.read("Build-Task3.xml").decode("utf-8") == build, "an inactive task is left alone"


def test_a_retest_that_names_no_template_gets_the_chart_too(tmp_path: Path) -> None:
    """The second chart is the project's strategies' need, not the task's template's."""
    build = TASK.format(tpl=template(tmp_path, [1440]))
    retest = f'<Task><Setups><Setup engine="x">{CHART}</Setup></Setups></Task>'
    extra = charts.streams({"config.xml": b"", "Build-Task3.xml": build.encode(),
                            "Retest-Task1.xml": retest.encode()})
    assert extra == [1440]
    assert charts.missing(retest, extra), "a one-chart retest of two-chart strategies"
    out, added = charts.ensure(retest, extra)
    assert added == 1 and charts.missing(out, extra) == []
    assert "D1 chart" not in out, "a retest has no builder chart list to extend"
