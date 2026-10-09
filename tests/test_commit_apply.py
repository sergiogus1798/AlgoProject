"""tools/commit_apply on a throwaway git repo: a normal apply, a path changed after the proposal, --only, a clean tree."""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.commit_apply import apply, status


def git(repo: Path, *args: str) -> str:
    """Run git in the temp repo."""
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout


def make_repo(tmp: Path) -> Path:
    """A repo with one commit and three uncommitted files in three themes."""
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@t")
    git(repo, "config", "user.name", "t")
    (repo / "a.py").write_text("1\n")
    git(repo, "add", "a.py")
    git(repo, "commit", "-q", "-m", "base")
    (repo / "a.py").write_text("2\n")
    (repo / "b.md").write_text("b\n")
    (repo / "c.txt").write_text("c\n")
    return repo


def proposal(tmp: Path, groups: list[dict]) -> Path:
    """Write a proposal file stamped one minute ago, so later edits count as «after»."""
    f = tmp / "p.json"
    f.write_text(json.dumps({"groups": groups, "en_curso": []}))
    t = time.time() - 60
    os.utime(f, (t, t))
    return f


def groups() -> list[dict]:
    """Three groups, one file each."""
    return [{"message": "one", "body": "why one", "paths": ["a.py"]},
            {"message": "two", "body": "", "paths": ["b.md"]},
            {"message": "three", "body": "", "paths": ["c.txt"]}]


def old(repo: Path, *paths: str) -> None:
    """Make files older than the proposal, as the proposer saw them."""
    t = time.time() - 3600
    for p in paths:
        os.utime(repo / p, (t, t))


def kw() -> dict:
    """Common flags: no push (there is no remote)."""
    return {"push": False}


def test_normal(tmp: Path) -> None:
    """Every group becomes its own commit with only its file, plus the trailer when passed."""
    repo = make_repo(tmp)
    old(repo, "a.py", "b.md", "c.txt")
    assert apply(proposal(tmp, groups()), repo, trailer="Co-Authored-By: X", **kw()) == 0
    assert git(repo, "log", "--format=%s").split() == ["three", "two", "one", "base"]
    assert git(repo, "show", "--name-only", "--format=", "HEAD~1").strip() == "b.md"
    assert "why one" in git(repo, "log", "--format=%B", "-1", "HEAD~2")
    assert "Co-Authored-By: X" in git(repo, "log", "--format=%B", "-1")
    assert status(repo) == {}


def test_changed_after(tmp: Path) -> None:
    """A file touched after the proposal skips its group; the others go; --force takes it."""
    repo = make_repo(tmp)
    old(repo, "a.py", "c.txt")
    f = proposal(tmp, groups())
    (repo / "b.md").write_text("b changed\n")
    assert apply(f, repo, **kw()) == 0
    assert git(repo, "log", "--format=%s").split() == ["three", "one", "base"]
    assert set(status(repo)) == {"b.md"}
    assert apply(f, repo, force=True, **kw()) == 0
    assert git(repo, "log", "--format=%s", "-1").strip() == "two"


def test_only_and_dry_run(tmp: Path) -> None:
    """--only commits the named group alone; a dry run commits nothing."""
    repo = make_repo(tmp)
    old(repo, "a.py", "b.md", "c.txt")
    f = proposal(tmp, groups())
    apply(f, repo, dry=True, **kw())
    assert len(git(repo, "log", "--format=%s").split()) == 1
    apply(f, repo, only={2}, **kw())
    assert git(repo, "log", "--format=%s").split() == ["two", "base"]
    assert set(status(repo)) == {"a.py", "c.txt"}


def test_stale_and_clean(tmp: Path) -> None:
    """A proposal past the age limit is refused; on a clean tree every group reads «ya commiteado»."""
    repo = make_repo(tmp)
    old(repo, "a.py", "b.md", "c.txt")
    f = proposal(tmp, groups())
    t = time.time() - 20 * 3600
    os.utime(f, (t, t))
    assert apply(f, repo, **kw()) == 2
    assert len(git(repo, "log", "--format=%s").split()) == 1
    git(repo, "add", "a.py", "b.md", "c.txt")
    git(repo, "commit", "-q", "-m", "all")
    assert apply(f, repo, force=True, **kw()) == 0
    assert len(git(repo, "log", "--format=%s").split()) == 2


def main() -> None:
    """Run each case in its own temp dir."""
    for case in (test_normal, test_changed_after, test_only_and_dry_run, test_stale_and_clean):
        with tempfile.TemporaryDirectory() as d:
            case(Path(d))
        print("ok", case.__name__)


if __name__ == "__main__":
    main()
