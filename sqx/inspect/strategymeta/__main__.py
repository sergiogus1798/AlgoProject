"""Print one strategy's metadata as JSON: `python3 -m sqx.inspect.strategymeta <file.sqx>`."""

import argparse
import json
from pathlib import Path

from sqx.inspect.strategymeta import read


def main() -> None:
    """Read one .sqx, and optionally its project.cfx, and print the dict."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sqx", type=Path, help="a .sqx, normally inside a databank folder")
    ap.add_argument("--cfx", type=Path, help="the project.cfx owning that databank")
    a = ap.parse_args()
    print(json.dumps(read(a.sqx, a.cfx), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
