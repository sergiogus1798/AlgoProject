#!/usr/bin/env python3
"""Golden-file test for core.cfx: a parser that breaks silently poisons every analysis."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import cfx

FIXTURE = Path(__file__).parent / "fixtures" / "optimizer.cfx"
GOLDEN = Path(__file__).parent / "fixtures" / "optimizer.golden.json"


def parse() -> dict:
    """Everything core.cfx reads out of the fixture project.

    Returns:
        Task list, each task's output databank, and its conditions.
    """
    tasks = cfx.tasks(str(FIXTURE))
    return {"tasks": tasks,
            "detail": [{"n": t["n"],
                        "output": cfx.output_databank(cfx.task_xml(str(FIXTURE), t["file"])),
                        "conditions": cfx.conditions(cfx.task_xml(str(FIXTURE), t["file"]))}
                       for t in tasks]}


def main() -> None:
    """Compare against the golden file, or write it when run with --bless."""
    result = parse()
    if "--bless" in sys.argv:
        GOLDEN.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"blessed {GOLDEN}")
        return
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    if result == expected:
        print("test_cfx: ok")
        return
    print("test_cfx: FAILED — core.cfx no longer reads this project the same way")
    print(json.dumps(result, indent=2)[:2000])
    sys.exit(1)


if __name__ == "__main__":
    main()
