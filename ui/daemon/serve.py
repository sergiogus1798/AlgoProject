#!/usr/bin/env python3
"""Run the daemon on loopback. The window starts it; this is also how to run it by hand."""

import argparse
import os
import socket
import sys

import uvicorn
from uvicorn.supervisors import ChangeReload

from core import uitoken
from core.paths import UI_PORT
from ui.daemon import gate


def main() -> None:
    """Bind the daemon to localhost and serve until killed."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=UI_PORT, help=f"default {UI_PORT}")
    ap.add_argument("--reload", action="store_true", help="restart on a code change")
    args = ap.parse_args()
    # 127.0.0.1 and never 0.0.0.0: this process can rewrite the library's CSVs, so it is
    # not something to put on the network of a machine that also runs three SQX installs.
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("127.0.0.1", args.port))
    except OSError as taken:
        sys.exit(f"el puerto {args.port} no está libre ({taken}): ¿ya hay un demonio?")
    sock.set_inheritable(True)
    # Only now, holding the port: a second daemon that lost the port must not replace the
    # token of the one that serves. The app reads it when imported (`gate.install`).
    uitoken.mint(args.port)
    os.environ[gate.ENV] = str(args.port)
    config = uvicorn.Config(
        "ui.daemon.app:APP",
        host="127.0.0.1",
        port=args.port,
        reload=args.reload,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    if args.reload:
        ChangeReload(config, target=server.run, sockets=[sock]).run()
    else:
        server.run(sockets=[sock])


if __name__ == "__main__":
    main()
