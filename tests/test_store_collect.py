#!/usr/bin/env python3
"""collect's races and hangs (encargo 76 E): the registry append waits for the registry's lock, temps carry the PID, rsync gives up."""

import fcntl
import os
import threading
import time
from pathlib import Path

import pytest

from core.store import collect
from tests.test_gorilla_collect import plant


def test_registry_append_waits_for_the_registry_lock(tmp_path: Path) -> None:
    """While a builder holds `registry.csv.lock`, collect does not write the registry."""
    gor, here = tmp_path / "gorilla", tmp_path / "here"
    plant(gor)
    (here / "store").mkdir(parents=True)
    (here / "projects").mkdir()
    lock = (here / "projects" / "registry.csv.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX)
    done: list[str] = []
    t = threading.Thread(
        target=lambda: done.append(collect._registry("Test_A", f"{gor}/", here, False))
    )
    t.start()
    time.sleep(0.3)
    assert not done and not (here / "projects" / "registry.csv").exists()
    lock.close()
    t.join(5)
    assert done and done[0].startswith("traída")


def test_temps_carry_the_pid_and_rsync_has_a_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two collects never share a temp name; a silent gorilla ends the rsync and the ssh."""
    gor, here = tmp_path / "gorilla", tmp_path / "here"
    plant(gor)
    seen: list[str] = []
    real = collect._rsync

    def spy(src: str, dest: Path, *extra: str) -> None:
        """Record where each rsync lands, then run it."""
        seen.append(str(dest))
        real(src, dest, *extra)

    monkeypatch.setattr(collect, "_rsync", spy)
    collect.collect(collect.listing("Test_A", gor), f"{gor}/", here)
    assert any(f".collect-{os.getpid()}-" in s for s in seen)
    assert "--timeout=50" in collect.RSYNC
    assert "ServerAliveInterval=10" in os.environ["RSYNC_RSH"]
