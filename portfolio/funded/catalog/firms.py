"""The firms register: which prop firms the project follows, and whether each is in the studies (`AlgoData/funding/firms.yaml`)."""

import yaml

from core.datapaths import funding_dir

# candidate: followed (catalogue, rules, deals) while the admission protocol runs; not in the studies.
# active: admitted by the owner; in the buying universe and the studies. rejected: no longer followed.
FOLLOWED = ("active", "candidate")


def load() -> list[dict]:
    """Every firm on the register, in file order."""
    return yaml.safe_load((funding_dir() / "firms.yaml").read_text(encoding="utf-8"))


def named(*statuses: str) -> list[str]:
    """The firm ids with one of these statuses."""
    return [f["firm"] for f in load() if f["status"] in statuses]
