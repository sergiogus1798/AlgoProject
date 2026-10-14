"""Rule 12 on one git command: one folder, one branch, staging by name — for guard.py."""

import re

VALUED = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--super-prefix",
    "--config-env",
}
WHOLE = {
    ".",
    "..",
    "*",
    ":",
    ":/*",
    ":(top)",
    "$PWD",
    "${PWD}",
    "__SUB__",
}  # after rstrip("/")
ADD_ALL = re.compile(r"--all|--update|--no-ignore-removal|-[a-zA-Z]*[Au][a-zA-Z]*")
COMMIT_ALL = re.compile(r"--all|-[a-zA-Z]*a[a-zA-Z]*")
COMMIT_VALUED = re.compile(
    r"--(message|file|author|date|reuse-message|reedit-message|fixup|squash"
    r"|template)|-[a-zA-Z]*[mFCct]"
)
BRANCH_CHANGES = re.compile(r"--(delete|move|copy|force)|-[a-zA-Z]*[dDmMcCf][a-zA-Z]*")
BRANCH_VALUED = {
    "--contains",
    "--no-contains",
    "--merged",
    "--no-merged",
    "--points-at",
    "--sort",
    "--format",
}
BRANCH_LISTS = re.compile(r"--list|-[a-zA-Z]*l[a-zA-Z]*")
CHECKOUT_BRANCHES = {"-b", "-B", "--orphan", "-t", "--track", "--detach"}

STAGE = "rule 12: stage only this task's files by name — never `git add -A` / `-u` / `git add .`"
COMMIT = "rule 12: stage this task's files by name, then commit — never `git commit -a`"
BRANCH = "rule 12: one branch — never create, delete or switch a branch"
CHECKOUT = (
    "rule 12: one branch — `git checkout` only to restore files: "
    "`git checkout [<ref>] -- <file>`"
)
FOLDER = (
    "rule 12: one folder — never `git worktree` (only `list`) and never a second clone"
)


def _add(rest: list[str], root: str) -> str | None:
    """`git add` of everything: by flag, or by a pathspec that names the whole tree."""
    cut = rest.index("--") if "--" in rest else len(rest)
    paths = rest[cut + 1 :] + [a for a in rest[:cut] if not a.startswith("-")]
    if any(ADD_ALL.fullmatch(a) for a in rest[:cut]):
        return STAGE
    return STAGE if any(p.rstrip("/") in WHOLE | {root} for p in paths) else None


def _commit(rest: list[str]) -> str | None:
    """`git commit -a`, alone or inside combined short flags; a message is never read as a flag."""
    valued = False
    for arg in rest:
        if arg == "--":
            break
        if not valued and COMMIT_ALL.fullmatch(arg):
            return COMMIT
        valued = not valued and bool(COMMIT_VALUED.fullmatch(arg))
    return None


def _branch(rest: list[str]) -> str | None:
    """`git branch` that creates, deletes, renames or copies; the listing forms pass."""
    lists, valued = False, False
    for arg in rest:
        if valued:
            valued = False
        elif arg in BRANCH_VALUED:
            valued = True
        elif BRANCH_CHANGES.fullmatch(arg):
            return BRANCH
        elif arg.startswith("-"):
            lists = lists or bool(BRANCH_LISTS.fullmatch(arg))
        elif not lists:
            return BRANCH
    return None


def _checkout(rest: list[str]) -> str | None:
    """Any `git checkout` that is not a file restore with an explicit `--`."""
    restores = "--" in rest and rest[rest.index("--") + 1 :]
    return None if restores and not CHECKOUT_BRANCHES & set(rest) else CHECKOUT


def git(words: list[str], root: str) -> str | None:
    """The reason rule 12 forbids this git command, or None.

    Args:
        words: The command's shell words, `git` first; global options (`-C <p>`, `-c <k=v>`…) may
            precede the subcommand.
        root: The repository's root, a pathspec that means "everything".
    """
    i = 1
    while i < len(words) and words[i].startswith("-"):
        i += 2 if words[i] in VALUED else 1
    sub, rest = (words[i : i + 1] or [""])[0], words[i + 1 :]
    if sub == "add":
        return _add(rest, root)
    if sub == "commit":
        return _commit(rest)
    if sub == "branch":
        return _branch(rest)
    if sub == "checkout":
        return _checkout(rest)
    if sub == "switch":
        return BRANCH
    if sub == "clone" or (sub == "worktree" and rest[:1] != ["list"]):
        return FOLDER
    return None
