"""What the control runs on: its knobs, the real population's harvest, and the chain's rules."""

from pathlib import Path

import yaml

from core.study import config as study_config
from engines.nulls import inputs as null_inputs
from pipeline.autopilot import judge
from studies.screening.gate import inputs as gate_inputs

CONFIG = Path(__file__).with_name("config.yaml")


def config(overrides: list[str]) -> dict:
    """The study's knobs, with `--set section.key=value` overrides applied."""
    return study_config.load(CONFIG, overrides)


def load(project: str, databank: str, feed: str, seed: int | None, rules: Path) -> dict:
    """The real population and everything the monkeys share with it.

    Args:
        project: The real population's project.
        databank: The databank its gate harvest is filed under.
        feed: Its SQX feed, e.g. "USDJPY_M1".
        seed: Root of the monkeys' random streams; None draws a fresh one.
        rules: The criteria file the chain is judged by.

    Returns:
        `real`, the harvest as the gate reads it (with `bars` and `market`); `gate_cfg` and
        `nullcfg`, the gate's and the null engine's own configs; `steps`, the rules; `tags`,
        what a rule's `by` may name; and `source`, what the manifest records. The donors
        are every strategy the harvest pairs: what conditions that databank carried is in
        the harvest's own manifest, named in `source`.
    """
    gate_cfg = gate_inputs.config([])
    folder = gate_inputs.newest(project, databank)
    real = gate_inputs.load(folder)
    timeframe = gate_inputs.timeframe(real["metrics"], gate_cfg, [])
    real["bars"] = null_inputs.bars(feed, timeframe)
    real["market"] = gate_inputs.market(feed)
    nullcfg = null_inputs.config(null_inputs.seeded(seed))
    parsed = yaml.safe_load(rules.read_text(encoding="utf-8"))
    return {"real": real, "gate_cfg": gate_cfg, "nullcfg": nullcfg, "steps": parsed["steps"],
            "tags": judge.tags(project) | {timeframe},
            "source": {"project": project, "databank": databank, "feed": feed,
                       "timeframe": timeframe, "harvest": str(folder), "split": real["split"],
                       "end": real["end"], "criteria": str(rules),
                       "frozen": bool(parsed.get("frozen")), "seed": nullcfg["nulls"]["seed"]}}
