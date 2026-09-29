#!/usr/bin/env python3
"""Known-answer test for sqx.inspect.project_map: an inactive task runs nothing in SQX,
so it must not appear as live in databank_flow(), tldr()'s loop/at-risk/terminal lines, or
task_order()'s [INACTIVE] flag. OPEN.md #10."""

import sys
from pathlib import Path
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.inspect import project_map

CONFIG = """<Project>
  <Databanks>
    <Databank name="Pool" view="v" syncType="onTimer" position="1"/>
    <Databank name="Out" view="v" syncType="never" position="2"/>
  </Databanks>
  <Tasks>
    <Task name="Build" title="Build" type="Build" active="true" taskXMLFile="t1.xml"/>
    <Task name="Clear" title="Clear (off)" type="ClearDatabanks" active="false" taskXMLFile="t2.xml"/>
    <Task name="Loop" title="Loop (off)" type="GoToTask" active="false" taskXMLFile="t3.xml"/>
  </Tasks>
</Project>
"""

# Task 1 (Build, active): writes Pool.
T1 = '<Task><Databanks><Databank name="Output" value="Pool"/></Databanks></Task>'
# Task 2 (ClearDatabanks, INACTIVE): would clear Pool while it auto-syncs — must not count.
T2 = '<Task><ClearDatabanks><Databank name="Pool"/></ClearDatabanks></Task>'
# Task 3 (GoToTask, INACTIVE): would loop unconditionally back to task 1 — must not count.
T3 = '<Task><GoToTask task="Build"/></Task>'

TASK_XML = {1: ElementTree.fromstring(T1), 2: ElementTree.fromstring(T2),
            3: ElementTree.fromstring(T3)}


def main() -> None:
    """Run the known-answer checks and exit non-zero on any failure."""
    cfg = ElementTree.fromstring(CONFIG)
    flow = project_map.databank_flow(cfg, TASK_XML)
    tldr = project_map.tldr(cfg, TASK_XML, flow)
    order = project_map.task_order(cfg, TASK_XML)

    failures = []

    # The inactive ClearDatabanks task must not clear Pool: Pool has no "cleared" entry.
    if flow.get("Pool", {}).get("cleared"):
        failures.append(f"Pool reads cleared by an inactive task: {flow['Pool']}")

    # Pool is written (task 1) and never read or cleared by anything ACTIVE -> terminal.
    # It must show up as terminal since the only thing that would exclude it (the
    # inactive clear) does not run.
    tldr_text = "\n".join(tldr)
    if "Pool" not in tldr_text.split("Terminal output databanks")[-1]:
        failures.append("Pool not reported as a terminal output databank:\n" + tldr_text)

    # 2 of 3 tasks inactive.
    if "3 tasks**, 2 inactive" not in tldr_text:
        failures.append("task/inactive count wrong:\n" + tldr_text)

    # The inactive GoToTask loop must not be reported as a live (even conditional) loop.
    if "loops back to" in tldr_text:
        failures.append("an inactive GoToTask was reported as a live loop:\n" + tldr_text)

    order_text = "\n".join(order)
    if "Loop (off)" not in order_text or "[INACTIVE]" not in order_text:
        failures.append("task_order lost the [INACTIVE] flag:\n" + order_text)

    if failures:
        print("test_project_map: FAILED")
        for f in failures:
            print(" -", f)
        sys.exit(1)
    print("test_project_map: ok")


if __name__ == "__main__":
    main()
