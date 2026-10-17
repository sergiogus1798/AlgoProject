"""core.proc.run: the deadline is enforced and a failure raises unless asked not to."""

import subprocess

import pytest

from core import proc


def test_timeout_raises() -> None:
    """A child past its deadline is killed and TimeoutExpired raised."""
    with pytest.raises(subprocess.TimeoutExpired):
        proc.run(["sleep", "5"], timeout=0.1)


def test_check_raises_unless_disabled() -> None:
    """A non-zero exit raises by default and returns with check=False."""
    with pytest.raises(subprocess.CalledProcessError):
        proc.run(["false"], timeout=10)
    assert proc.run(["false"], timeout=10, check=False).returncode == 1
