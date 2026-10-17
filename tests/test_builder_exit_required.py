"""L1 B (owner, 2026-10-16): `exit_required` forces the condition exit on one project's Build,
leaving `_build.yaml` (condition_required: false) untouched for every other project."""

import re

from core.assetdata import doctrine, load
from core.datapaths import projects_backup
from sqx.projects import cfxio
from sqx.projects import doctrine as rules_of

DONOR = projects_backup("XAUUSD_base_2026-09-21") / "project.cfx"


def exit_rule_odds(required: bool) -> set[str]:
    """The probability every `_ExitRule_` block of the donor's Build gets."""
    build = next(
        b.decode("utf-8")
        for n, b in cfxio.members(DONOR).items()
        if n.endswith(".xml") and b"<Blocks" in b
    )
    text, _ = rules_of.apply_doctrine(build, load("XAUUSD"), "build", "H1", required)
    return set(re.findall(r'<Block key="_ExitRule_"[^>]*?probability="(\d+)"', text))


def test_the_flag_makes_the_condition_exit_compulsory_only_where_asked() -> None:
    """Off: the doctrine's optional 50. On: 100. The yaml stays false."""
    assert not doctrine()["exits"]["condition_required"]
    assert exit_rule_odds(False) == {"50"} and exit_rule_odds(True) == {"100"}
