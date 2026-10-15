"""For a test that exists to check THIS machine's live data (its harvest, its archive): not a test itself.

`require(path, reason)` at the top of the test: where `path` is missing (gorilla holds only the market data)
the test prints the marker line below and stops with exit 0. `tools/audit_tests.py` lists every test whose
output carries the marker under «apartadas en esta máquina», so a skip is never silent (encargo 71, D1).
"""

import functools
import os
import sys
from collections.abc import Callable
from pathlib import Path

MARKER = "APARTADA EN ESTA MÁQUINA"


def require(path: Path, reason: str) -> None:
    """Stop the test, successfully and loudly, when the live data it validates is not here.

    Args:
        path: A file or folder only the machine that owns the live data has.
        reason: Why the test needs it, in Spanish: it is printed in the audit.
    """
    if Path(path).exists():
        return
    message = f"{MARKER}: {reason} (falta {path})"
    if "pytest" in sys.modules:
        import pytest

        pytest.skip(message, allow_module_level=True)
    print(message)
    sys.exit(0)


def only_here(path: Path, reason: str) -> Callable:
    """Decorator for ONE test of a file that checks this machine's live data; the rest of the file still runs.

    Where `path` is missing the test prints the marker line and returns (pytest: skips it), so the
    audit lists it under «apartadas en esta máquina» while the file's other tests keep their verdict.

    Args:
        path: A file or folder only the machine that owns the live data has.
        reason: Why the test needs it, in Spanish: it is printed in the audit.

    Returns:
        The decorator.
    """

    def wrap(test: Callable) -> Callable:
        """Guard one test."""

        @functools.wraps(test)
        def guarded(*args: object, **kwargs: object) -> object:
            """Run the test only where its live data exists."""
            if Path(path).exists():
                return test(*args, **kwargs)
            message = f"{MARKER}: {reason} (falta {path})"
            if "PYTEST_CURRENT_TEST" in os.environ:
                import pytest

                pytest.skip(message)
            print(message)
            return None

        return guarded

    return wrap
