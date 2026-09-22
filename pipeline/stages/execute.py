"""Run one stage as its own process and turn what it prints into ledger progress."""

import hashlib
import json
import subprocess
from pathlib import Path

from core.paths import ROOT
from pipeline.ledger import progress, state


def parse(line: str, marker: str) -> tuple[int, str] | None:
    """Read one line of a stage's output as a progress report, if it is one.

    Args:
        line: A line the stage printed, without its newline.
        marker: The protocol word from config.yaml, e.g. "PROGRESS".

    Returns:
        (percentage, status line), or None when the line is ordinary output. The protocol
        is "PROGRESS <0..100> <text>" and it is the entire coupling between this pipeline
        and the modules it chains: a stage joins by adding one print, not an import.
    """
    parts = line.split(maxsplit=2)
    if len(parts) < 2 or parts[0] != marker or not parts[1].isdigit():
        return None
    return int(parts[1]), parts[2] if len(parts) > 2 else ""


def stream(stage: dict, work: Path, marker: str) -> None:
    """Run the stage's command, reporting into the ledger line by line as it goes.

    Args:
        stage: A resolved recipe row.
        work: The strategy's work directory.
        marker: The protocol word from config.yaml.

    Raises:
        SystemExit: The command exited non-zero. Its output has already been streamed to
            the terminal, so the traceback the stage printed is the message.

    Stdout is consumed as it arrives rather than at the end: a stage that runs forty
    minutes and says nothing until it finishes is indistinguishable from a hung one.
    """
    name = stage["name"]
    with subprocess.Popen(stage["command"], cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, bufsize=1) as proc:
        for line in proc.stdout:
            line = line.rstrip("\n")
            print(f"   | {line}")
            found = parse(line, marker)
            if found:
                progress.say(work, name, *found)
            elif line.strip():
                progress.note(work, name, line.strip())
    if proc.returncode:
        raise SystemExit(f"{name}: exited {proc.returncode}")


def recorded(stage: dict) -> dict:
    """The fields the recipe asks to lift from the stage's output into the ledger.

    Args:
        stage: A resolved recipe row.

    Returns:
        The named top-level fields of the row's `record_from` file, or nothing when the
        row asks for none. This is how `stages.collected.removable` reaches the ledger,
        which is what perf/disk/retention.py reads to call a deletion provable rather
        than likely, and how the SPP verdict reaches `stages.sppultra.verdict`.
    """
    wanted = stage.get("record")
    if not wanted:
        return {}
    got = json.loads(stage["record_from"].read_text(encoding="utf-8"))
    return {field: got[field] for field in wanted}


def hashed(stage: dict) -> dict:
    """Fingerprints of the files the recipe asks the ledger to remember.

    Args:
        stage: A resolved recipe row.

    Returns:
        One sha256 per entry of the row's `hash` map. `brief_hash` is the one that
        matters: it names *which* design the later stages were built from, so a brief
        that changed afterwards can be caught instead of quietly producing 5,000 variants
        of one design judged against the numbers of another.
    """
    return {field: hashlib.sha256(path.read_bytes()).hexdigest()
            for field, path in stage["hash"].items()}


def run(stage: dict, work: Path, marker: str) -> None:
    """Start a stage, follow it, and close its ledger entry.

    Args:
        stage: A resolved recipe row.
        work: The strategy's work directory.
        marker: The protocol word from config.yaml.
    """
    state.begin(work, stage["name"])
    stream(stage, work, marker)
    state.finish(work, stage["name"], recorded(stage) | hashed(stage))
