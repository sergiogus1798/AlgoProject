"""Split a shell command line into the simple commands it would run, for guard.py."""

import re
import shlex
from pathlib import Path

OPS = "();<>|&\n"
SUB = "__SUB__"  # stands where a `$(…)` or a backtick body was lifted out of a word
# A heredoc: its body is data handed to the command, so it becomes one quoted argument of it.
HEREDOC = re.compile(
    r"(?<!<)<<(?!<)-?[ \t]*(['\"]?)(\w+)\1([^\n]*)\n(.*?)\n[ \t]*\2[ \t]*(?=\n|$)", re.S
)
FD = re.compile(r"(?<=[\s;|&(])\d(?=[<>])")  # the 2 of `2>/dev/null` is not an argument
SHELLS = {"sh", "bash", "zsh", "dash", "eval"}
WRAPPERS = {
    "sudo",
    "env",
    "nohup",
    "time",
    "command",
    "builtin",
    "exec",
    "nice",
    "ionice",
    "setsid",
    "stdbuf",
    "timeout",
    "xargs",
    "{",
    "}",
    "!",
    "if",
    "then",
    "else",
    "elif",
    "while",
    "until",
    "do",
}
ASSIGN = re.compile(r"\w+=.*", re.S)
SKIPPED = re.compile(
    r"-.*|\d+(\.\d+)?[smhd]?|\w+=.*|\{\}", re.S
)  # a wrapper's own arguments


def _close(cmd: str, start: int) -> int:
    """Index of the parenthesis that closes the `$(` whose body starts at `start`."""
    depth, quote = 1, ""
    for j in range(start, len(cmd)):
        if quote or cmd[j] in "'\"":
            quote = "" if cmd[j] == quote else quote or cmd[j]
            continue
        depth += (cmd[j] == "(") - (cmd[j] == ")")
        if not depth:
            return j
    raise ValueError("unclosed $(")


def _lift(cmd: str) -> tuple[str, list[str]]:
    """Take comments and command substitutions out of a command line.

    Returns:
        The line with each unquoted `# …` dropped and each `$(…)` or backtick body outside single
        quotes replaced by SUB, and those bodies. Raises ValueError on an unclosed one.
    """
    out, inner, i, quote = [], [], 0, ""
    while i < len(cmd):
        c = cmd[i]
        if quote == "'":
            quote = "" if c == "'" else quote
        elif c == "\\":
            out.append(cmd[i : i + 2])
            i += 2
            continue
        elif c == quote or (c in "'\"" and not quote):
            quote = "" if quote else c
        elif c == "#" and not quote and (i == 0 or cmd[i - 1] in " \t\n;"):
            i = cmd.find("\n", i) if "\n" in cmd[i:] else len(cmd)
            continue
        elif c == "`" or cmd.startswith("$(", i):
            start = i + (1 if c == "`" else 2)
            end = cmd.index("`", start) if c == "`" else _close(cmd, start)
            inner.append(cmd[start:end])
            out.append(SUB)
            i = end + 1
            continue
        out.append(c)
        i += 1
    return "".join(out), inner


def _lex(text: str) -> list[str]:
    """Shell words of a line, operators and newlines as tokens of their own."""
    lex = shlex.shlex(FD.sub("", text), posix=True, punctuation_chars=OPS)
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    lex.commenters = ""
    return list(lex)


def _operator(token: str) -> bool:
    """Whether a token is made of shell operator characters only."""
    return bool(token) and not set(token) - set(OPS)


def _simple(words: list[str]) -> list[tuple[list[str], list[str]]]:
    """One simple command, its redirections and wrappers taken off, and what a shell in it runs."""
    args, writes, i = [], [], 0
    while i < len(words):
        if _operator(words[i]):
            if ">" in words[i]:
                writes += words[i + 1 : i + 2]
            i += 2
            continue
        args.append(words[i])
        i += 1
    while args and (args[0] in WRAPPERS or ASSIGN.fullmatch(args[0])):
        wrapper = args.pop(0) in WRAPPERS
        while wrapper and args and SKIPPED.fullmatch(args[0]):
            args.pop(0)
    if not args and not writes:
        return []
    out = [(args or [":"], writes)]
    if Path(out[0][0][0]).name in SHELLS:
        for arg in args[1:]:
            out += commands(arg)
    return out


def commands(cmd: str) -> list[tuple[list[str], list[str]]]:
    """The simple commands a shell line runs: split on `;`, `&&`, `||`, `|`, newlines, subshells.

    A quoted string is one word of the command it is passed to — data, not a command — except the
    arguments of sh/bash/eval and what `$(…)` or backticks hold, which are parsed as commands too.

    Args:
        cmd: The command line as Bash receives it.

    Returns:
        One (words, redirection write targets) per command, the command word first, wrappers
        (`sudo`, `env X=1`, `xargs`, `then`…) removed. Raises ValueError on unbalanced quoting.
    """
    text, inner = _lift(
        HEREDOC.sub(lambda m: shlex.quote(m[4]) + m[3], cmd.replace("\\\n", " "))
    )
    out, words = [], []
    for token in [*_lex(text), ";"]:
        if _operator(token) and ("(" in token or not set(token) & set("<>")):
            out += _simple(words)
            words = []
        else:
            words.append(token)
    for body in inner:
        out += commands(body)
    return out
