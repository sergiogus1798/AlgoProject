#!/usr/bin/env python3
"""harness.write touches only the task its `kind` names by title, never another task's."""

import sys
import tempfile
import zipfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.variants import harness

# A synthetic workflow project: five tasks, the trap being that "Retest-Task1.xml" -- the
# file name the pre-2026-09-29 code always overwrote -- is the real `OOS` task here, not a
# spare slot. "SPP IS" and "SPP OOS" sit on different file names entirely, as
# `sqx.projects.builder --workflow` actually lays them out (kept from the frozen donor).
CONFIG = """<Project name="Trade_XAUUSD">
  <Tasks>
    <Task taskXMLFile="Build-Task3.xml" title="CONSTRUCCION" active="true" type="Build" />
    <Task taskXMLFile="Retest-Task1.xml" title="OOS" active="true" type="Retest" />
    <Task taskXMLFile="Retest-Task13.xml" title="SPP IS" active="false" type="Retest" />
    <Task taskXMLFile="Retest-Task14.xml" title="SPP OOS" active="false" type="Retest" />
    <Task taskXMLFile="Retest-Task2.xml" title="WFM" active="false" type="Retest" />
  </Tasks>
</Project>
"""
MEMBERS = {
    "config.xml": CONFIG.encode("utf-8"),
    "Build-Task3.xml": b"<Task>original CONSTRUCCION</Task>",
    "Retest-Task1.xml": b"<Task>original OOS</Task>",
    "Retest-Task13.xml": b"<Task>original SPP IS</Task>",
    "Retest-Task14.xml": b"<Task>original SPP OOS</Task>",
    "Retest-Task2.xml": b"<Task>original WFM</Task>",
}


def build_cfx(path: Path, members: dict[str, bytes] = MEMBERS) -> None:
    """Write a synthetic project.cfx with the given members."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in members.items():
            z.writestr(name, blob)


def read_all(path: Path) -> dict[str, bytes]:
    """Every member of a project.cfx, as bytes."""
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}


def no_port(*_a, **_k) -> SimpleNamespace:
    """Stand in for `subprocess.run(["ss", "-ltn"], ...)`: no install is listening."""
    return SimpleNamespace(stdout="")


def check(failures: list, ok: bool, said: str) -> None:
    """Record one property and say how it went."""
    print(f"  {'ok  ' if ok else 'FALLA'} {said}")
    if not ok:
        failures.append(said)


def main() -> None:
    """Run every property, and raise if one of them broke."""
    failures: list[str] = []
    harness.subprocess.run = no_port   # no real install is ever consulted by this test

    with tempfile.TemporaryDirectory(prefix="sqx-harness-test-") as tmp:
        cfx = Path(tmp) / "project.cfx"
        build_cfx(cfx)

        harness.write(cfx, "<Task>new SPP IS</Task>", "spp_is", "custodian")
        after = read_all(cfx)
        check(failures, after["Retest-Task13.xml"] == b"<Task>new SPP IS</Task>",
              "kind=spp_is rewrites Retest-Task13.xml (titled SPP IS)")
        for name, blob in MEMBERS.items():
            if name == "Retest-Task13.xml":
                continue
            check(failures, after[name] == blob, f"kind=spp_is leaves {name} byte-identical")

        build_cfx(cfx)   # fresh copy: prove kind=spp_oos touches a DIFFERENT member
        harness.write(cfx, "<Task>new SPP OOS</Task>", "spp_oos", "custodian")
        after = read_all(cfx)
        check(failures, after["Retest-Task14.xml"] == b"<Task>new SPP OOS</Task>",
              "kind=spp_oos rewrites Retest-Task14.xml (titled SPP OOS)")
        check(failures, after["Retest-Task1.xml"] == MEMBERS["Retest-Task1.xml"],
              "kind=spp_oos never touches Retest-Task1.xml (the real OOS task, "
              "the pre-2026-09-29 hardcoded target)")
        for name, blob in MEMBERS.items():
            if name == "Retest-Task14.xml":
                continue
            check(failures, after[name] == blob, f"kind=spp_oos leaves {name} byte-identical")

        build_cfx(cfx)   # kind=retest targets "OOS", i.e. the real Retest-Task1.xml
        harness.write(cfx, "<Task>new OOS</Task>", "retest", "custodian")
        after = read_all(cfx)
        check(failures, after["Retest-Task1.xml"] == b"<Task>new OOS</Task>",
              "kind=retest rewrites Retest-Task1.xml (titled OOS)")
        for name, blob in MEMBERS.items():
            if name == "Retest-Task1.xml":
                continue
            check(failures, after[name] == blob, f"kind=retest leaves {name} byte-identical")

        # A project that never went through `builder --workflow` carries no SPP IS/SPP OOS
        # task at all -- refuse cleanly rather than guess a file name.
        no_spp = """<Project name="Test_XAUUSD">
  <Tasks>
    <Task taskXMLFile="Build-Task3.xml" title="CONSTRUCCION" active="true" type="Build" />
    <Task taskXMLFile="Retest-Task1.xml" title="OOS" active="true" type="Retest" />
  </Tasks>
</Project>
"""
        build_cfx(cfx, {"config.xml": no_spp.encode("utf-8"),
                        "Build-Task3.xml": MEMBERS["Build-Task3.xml"],
                        "Retest-Task1.xml": MEMBERS["Retest-Task1.xml"]})
        try:
            harness.write(cfx, "<Task>x</Task>", "spp_is", "custodian")
            check(failures, False, "missing SPP IS task refuses instead of guessing")
        except SystemExit:
            check(failures, True, "missing SPP IS task refuses instead of guessing")

    if failures:
        raise SystemExit(f"{len(failures)} fallo(s):\n" + "\n".join(failures))
    print("ok: harness.write touches only its own task, by title, on every kind")


if __name__ == "__main__":
    main()
