"""`.claude/hooks/stop_checks.py` blocks a stop only for a .py this session edited that ruff rejects."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "stop_checks.py"


def fire(stdin: str) -> str:
    """Run the hook on `stdin`; returns its stdout ('' = the stop goes through)."""
    p = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, p.stderr
    return p.stdout


def transcript(tmp: Path, *paths: Path) -> str:
    """Stdin JSON pointing at a transcript in which each path was edited."""
    rows = [{"message": {"content": [{"type": "tool_use", "name": "Edit", "input": {"file_path": str(p)}}]}}
            for p in paths]
    f = tmp / "t.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in rows))
    return json.dumps({"transcript_path": str(f)})


def main() -> None:
    """The four cases of the hook."""
    (ROOT / "scratch").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT / "scratch") as d:
        tmp = Path(d)
        bad = tmp / "bad_stop_check.py"
        bad.write_text("print(undefined_name_xyz)\n")
        assert fire(transcript(tmp, bad).replace("{", '{"stop_hook_active": true,', 1)) == ""
        assert fire(transcript(tmp)) == ""
        assert fire(transcript(tmp, tmp / "notes.txt")) == ""
        out = json.loads(fire(transcript(tmp, bad)))
        assert out["decision"] == "block" and "undefined_name_xyz" in out["reason"], out
        assert fire("not json") == ""
    print("test_stop_checks: ok")


if __name__ == "__main__":
    main()
