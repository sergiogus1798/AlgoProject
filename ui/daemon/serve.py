#!/usr/bin/env python3
"""Run the daemon on loopback. The window starts it; this is also how to run it by hand."""

import argparse

import uvicorn

from core.paths import UI_PORT


def main() -> None:
    """Bind the daemon to localhost and serve until killed."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=UI_PORT, help=f"default {UI_PORT}")
    ap.add_argument("--reload", action="store_true", help="restart on a code change")
    args = ap.parse_args()
    # 127.0.0.1 and never 0.0.0.0: this process can rewrite the library's CSVs, so it is
    # not something to put on the network of a machine that also runs three SQX installs.
    uvicorn.run("ui.daemon.app:APP", host="127.0.0.1", port=args.port,
                reload=args.reload, log_level="warning")


if __name__ == "__main__":
    main()
