"""Runs before anything else here: makes stdout/stderr able to print this project's own text.

Every report prints accents, em dashes and arrows. Windows' console defaults to a legacy
codepage (cp1252) that cannot encode most of them, so an ordinary print() crashes the run
after the work is already done and saved — tested, on `→` in a MC report's last line.
"""

import sys

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
