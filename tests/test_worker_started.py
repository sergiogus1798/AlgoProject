#!/usr/bin/env python3
"""`core.worker.started`: «Starting project» counts on any line of SQX's reply, and only for the project named."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.worker import started


def test_started_reads_the_whole_reply() -> None:
    """A log line before «Starting project» is still a start; a reply without it is a refusal."""
    started(
        "12:00:01 Loading databanks\n12:00:02 Starting project 'Test_A'\n", "Test_A"
    )
    for refused in ("", "Error: project not found", "Starting project 'Test_B'"):
        with pytest.raises(SystemExit):
            started(refused, "Test_A")
