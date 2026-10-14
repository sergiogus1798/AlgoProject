"""How many commands of one test a step runs at once (`ui.daemon.jobs.width`)."""

from ui.daemon import jobs


def test_picked_survivors_run_several_at_once() -> None:
    """A wide test runs alone on a population; once per picked survivor, PICKED of them at a time."""
    assert jobs.width("monkey", 1) == 1  # on the population it fans out itself
    assert jobs.width("monkey", 1352) == jobs.PICKED["monkey"]
    assert jobs.width("gate", 5) == 1
    assert jobs.width("entryQuality", 5) == jobs.SLOTS // jobs.LIGHT
