"""The operation routes: the custodian's pulse and the search ledger, both read-only."""

from fastapi import APIRouter

from ui.daemon.ops import ledgerview, pulse

ROUTER = APIRouter()


@ROUTER.get("/api/pulse")
def get_pulse() -> dict:
    """One reading of the custodian: count, rate, JVM against `-Xmx`, CPU, free RAM, warnings.

    Returns:
        `{"custodian": {...}}`. Reads /proc, today's SQX log, `sqcli.config` and the daemon's
        job logs; sends nothing to any install. Takes about half a second: the CPU figure
        is two samples of the process's clock ticks.
    """
    return {"custodian": pulse.custodian()}


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
