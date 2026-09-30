"""The operation routes: the custodian's pulse, what each worker runs, and the search ledger."""

from fastapi import APIRouter

from ui.daemon.ops import ledgerview, pulse, runs

ROUTER = APIRouter()


@ROUTER.get("/api/pulse")
def get_pulse() -> dict:
    """One reading of the custodian: count, rate, JVM against `-Xmx`, CPU, free RAM, warnings.

    Returns:
        `{"custodian": {...}}`. Reads /proc, today's SQX log, `sqcli.config` and the daemon's
        job logs; to a custodian whose log says a project runs it sends `-project
        action=status` (`runs.count`), and nothing else to any install. Takes about half a
        second: the CPU figure is two samples of the process's clock ticks.
    """
    return {"custodian": pulse.custodian()}


@ROUTER.get("/api/ops/sqx")
def get_sqx_runs() -> dict:
    """What each SQX worker runs right now, for the jobs strip and «En marcha».

    Returns:
        `{"runs": [...]}` as `runs.runs` builds them: project, task, done, total, percent.
        Files, plus `-project action=status` to a worker only while its log says it runs.
    """
    return {"runs": runs.runs()}


@ROUTER.get("/api/ledger")
def get_ledger(study: str = "") -> dict:
    """One study's search ledger: its searches, its funnel and the history it has spent.

    Args:
        study: A study id as `ledger.study.study_id` builds it; empty for the one written last.

    Returns:
        What `ledgerview.ledger` returns. An unknown id is refused in a sentence.
    """
    if study and study not in ledgerview.studymod.studies():
        return {"error": f"no hay ledger para «{study}»"}
    return ledgerview.ledger(study or None)
