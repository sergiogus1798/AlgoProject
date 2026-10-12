---
q: Can a CustomAnalysis snippet read or cut another project's databank in memory, and where should its task live?
kw: CustomAnalysis task XML, FullDatabank1, PerStrategy1, processDatabank, filterStrategy, InputArgs, ProjectEngine.get getDatabanks getRecords, Trade_AlgoTools, tool project, set_money_management crash task without MoneyManagement, curate databank from java, AlgoKeep, removeReports
tag: 🔬  date: 2026-10-12  see: snippets-compile-on-start
---
# A CustomAnalysis task reads any loaded project's databank — so it lives in ONE tool project, never in a workflow project
A `CustomAnalysis` task runs a snippet over a databank in memory, and what `processDatabank`
returns **is** the databank afterwards. Inside it `ProjectEngine.get(<project>).getDatabanks()
.get(<bank>).getRecords()` reads **any** loaded project, so the task lives in `Trade_AlgoTools`
(`sqx/snippets/toolproject.py`), its `InputArgs` rewritten by `updateTaskXML` before each start.
Never add one to a workflow project: 17 places in `sqx/projects/` treat every task as a backtest
(the builder died in `set_money_management`).

## Evidence
- 🔬 conductor, 2026-10-12, task XML (shape read from the owner's `AUDJPY/project.cfx`):
  `<CustomAnalysis><PerStrategy1/><FullDatabank1>NAME</FullDatabank1><InputArgs>…</InputArgs>
  <RemoveFailedStrategies>…</CustomAnalysis>` plus `<Databanks>` Input/Output; config line
  `<Task name="Custom analysis" type="CustomAnalysis" taskXMLFile="CustomAnalysis-Task1.xml" …/>`.
- 🔬 `AlgoKeep` returning the strategies named in a file: 1,000 → 10 in memory, and on disk after
  the sync.
- 🔬 `AlgoTrades` run from `Trade_AlgoTools` wrote the 1,000 trade lists of
  `Test_XAUUSD_H1_snippets/Results`, another project of the same session.

## Also
A task of type `CustomAnalysis` runs a snippet (`extends CustomAnalysisMethod`) over a databank
held in memory: `filterStrategy` per strategy, `processDatabank` over the whole list, and what
`processDatabank` returns **is** the databank afterwards (a subset really cuts it; disk follows on
the next sync or stop). Inside it, `ProjectEngine.get(<project>).getDatabanks().get(<bank>)
.getRecords()` gives the strategies of **any** project the session has loaded. So the task does
not have to sit in the project it serves: `Trade_AlgoTools` (`sqx/snippets/toolproject.py`) holds
one task, and its `InputArgs` — rewritten with `updateTaskXML` before each `start` — say whose
databank. Do not add such a task to a workflow project: 17 places in `sqx/projects/` treat every
member that is not `config.xml` as a backtest task (the builder died in `set_money_management` on
a task with no `<MoneyManagement>`).

Cutting a databank this way works but is not needed: `sqx.projects.live.cut`
(`/project/removeReports`) already does it in a live session, and `sqx.curate.apply_verdict` uses
it. A curation snippet was written, proven and deleted the same day.
