"""What a button runs, and the one place a finished analysis is held for the session."""

from core import manifest
from strategies.retest import run
from strategies.retest.measure import store

# The session's results, one entry per strategy. Deliberately memory only and with no
# fingerprint: unlike the sibling study, the expensive half of this one already happened at
# ingest, so re-running a strategy costs a second. A cache would buy nothing and would add a
# way to read a stored number as the answer to a question it was not computed for.
RESULTS: dict = {}


def keys(setup: dict) -> dict:
    """The three values every store call needs.

    Args:
        setup: SETUP, as serve.py's main() assembled it.

    Returns:
        {"project", "databank", "day"}.
    """
    return {k: setup[k] for k in ("project", "databank", "day")}


def provenance(setup: dict, strategy: str) -> dict:
    """What the ingest recorded about one strategy's eight runs.

    Args:
        setup: SETUP.
        strategy: One strategy id.

    Returns:
        {task: provenance}, from the ingest manifest.
    """
    return {task: got for key, got in setup["provenance"].items()
            for task, name in [key.split("/", 1)] if name == strategy}


def analyse(setup: dict, strategy: str) -> dict:
    """Run the four questions on one strategy and keep the result for the session.

    Args:
        setup: SETUP, with the cfg this request is scoped to.
        strategy: One strategy id.

    Returns:
        What run.one() returned.
    """
    sims = store.load_sims(**keys(setup))
    original = store.load_original(**keys(setup))
    got = run.one(keys(setup), sims, original, provenance(setup, strategy), strategy,
                  setup["cfg"])
    RESULTS[strategy] = got
    return got


def whole(setup: dict) -> dict:
    """Run every strategy, plus what can only be said across them.

    Args:
        setup: SETUP, with the cfg this request is scoped to.

    Returns:
        What run.battery() returned, with each strategy also kept individually.
    """
    got = run.battery(keys(setup), setup["provenance"], setup["cfg"])
    RESULTS.update(got["strategies"])
    return got


def load_provenance(setup: dict) -> dict:
    """The ingest manifest's task entries.

    Args:
        setup: SETUP, before scoping.

    Returns:
        {"task/strategy": provenance}. Read once at start-up: it describes the export on
        disk and no drawer override can change it.
    """
    return manifest.read(store.root(**keys(setup)))["source"]["tasks"]
