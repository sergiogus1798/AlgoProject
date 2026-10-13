"""The one-task project every worker carries to run the project's CustomAnalysis snippets from."""

from pathlib import Path
from xml.sax.saxutils import escape

from core.paths import worker_dir
from sqx.projects import cfxio

# The task lives in a project of its own and reads any other project's databank, so no
# workflow project carries a task that is not a backtest (17 places assume every task is one).
NAME = "Trade_AlgoTools"
MEMBER = "CustomAnalysis-Task1.xml"
CONFIG = f"""<?xml version='1.0' encoding='utf-8'?>
<Project name="{NAME}" version="142.2399">
  <Tasks>
    <Task name="Custom analysis" type="CustomAnalysis" taskXMLFile="{MEMBER}" title="Export trades" active="true" />
  </Tasks>
  <Databanks>
    <Databank name="Results" view="Default - Main data" syncType="Auto-sync every 1 hour" position="0" />
  </Databanks>
</Project>
"""
_SETTINGS = """<Settings>
  <CustomAnalysis>
    <PerStrategy1>none</PerStrategy1>
    <PerStrategy2>none</PerStrategy2>
    <FullDatabank1>{snippet}</FullDatabank1>
    <FullDatabank2>none</FullDatabank2>
    <RemoveFailedStrategies>false</RemoveFailedStrategies>
    <Filter>true</Filter>
    <InputArgsPerStrategy1 />
    <InputArgsPerStrategy2 />
    <InputArgsFullDatabank1>{args}</InputArgsFullDatabank1>
    <InputArgsFullDatabank2 />
  </CustomAnalysis>
  <Databanks>
    <Databank label="Input databank" name="Input" value="Results" />
    <Databank label="Output databank" name="Output" value="Results" />
  </Databanks>
</Settings>
"""


def settings(snippet: str, args: str) -> str:
    """The task's XML set to run one CustomAnalysis snippet over the whole databank.

    Args:
        snippet: The snippet's name, as its constructor gives it to SQX ("AlgoBank").
        args: Its `inputArgs`, as the snippet's own header documents them.
    """
    return _SETTINGS.format(snippet=snippet, args=escape(args))


def cfx(role: str) -> Path:
    """The tool project's .cfx on an install."""
    return worker_dir(role) / "user/projects" / NAME / "project.cfx"


def ensure(role: str) -> bool:
    """Create the tool project on a stopped install; whether it was missing."""
    file = cfx(role)
    if file.exists():
        return False
    (file.parent / "databanks/Results").mkdir(parents=True)
    cfxio.write(file, {"config.xml": CONFIG.encode("utf-8"),
                      MEMBER: settings("AlgoBank", "").encode("utf-8")})
    return True
