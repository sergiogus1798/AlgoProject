"""Close issues of OPEN.md, or add a dated note to one.

    python3 .claude/skills/open-close/close.py spec.json [--dry-run]

spec.json: {"close": {"<N>": ["<emoji>", "<note>"]}, "note": {"<N>": ["<emoji>", "<note>"]}}

A closed section moves verbatim to docs/OPEN-closed.md, in numeric order, with its heading emoji
flipped and `**Closed <today>.** <note>` appended; its index row points at the archive. A noted
section stays, with `**<today>.** <note>` appended and its emoji updated.
"""
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OPEN, CLOSED = ROOT / "OPEN.md", ROOT / "docs" / "OPEN-closed.md"
HEAD = re.compile(r"^## (\d+[a-z]?)\s*[.·]\s*(\S+)", re.M)


def sections(text: str) -> dict[str, tuple[int, int]]:
    """Where each numbered `## N` section starts and ends."""
    starts = [m.start() for m in re.finditer(r"^## ", text, re.M)]
    out = {}
    for i, s in enumerate(starts):
        m = HEAD.match(text, s)
        if m:
            out[m.group(1)] = (s, starts[i + 1] if i + 1 < len(starts) else len(text))
    return out


def flip(body: str, emoji: str) -> str:
    """The section with its heading emoji replaced."""
    return HEAD.sub(lambda m: m.group(0).replace(m.group(2), emoji), body, count=1)


def order(n: str) -> tuple[int, str]:
    """Sort key: 9 before 10, 10 before 10a."""
    return int(re.match(r"\d+", n).group()), n


args = [a for a in sys.argv[1:] if a != "--dry-run"]
if len(args) != 1:
    sys.exit(__doc__)
spec = json.loads(Path(args[0]).read_text(encoding="utf-8"))
close, note = spec.get("close", {}), spec.get("note", {})
day = datetime.date.today().isoformat()
op, cl = OPEN.read_text(encoding="utf-8"), CLOSED.read_text(encoding="utf-8")
sec, csec = sections(op), sections(cl)

missing = [n for n in list(close) + list(note) if n not in sec]
if missing or set(close) & set(note) or set(close) & set(csec):
    sys.exit(f"not an open section of OPEN.md: {missing}; in both close and note: "
             f"{sorted(set(close) & set(note))}; already in the archive: {sorted(set(close) & set(csec))}")

moved, noted = {}, {}
for n, (emoji, text) in close.items():
    s, e = sec[n]
    body = op[s:e].rstrip("\n").rstrip("-").rstrip()
    moved[n] = flip(body, emoji) + f"\n\n**Closed {day}.** {text}\n"
for n, (emoji, text) in note.items():
    s, e = sec[n]
    body, trail = op[s:e].rstrip("\n"), ""
    if body.endswith("---"):
        body, trail = body[:-3].rstrip(), "\n\n---"
    noted[n] = flip(body, emoji) + f"\n\n**{day}.** {text}{trail}\n\n"

pieces, last = [], 0
for n, (s, e) in sorted(sec.items(), key=lambda kv: kv[1][0]):
    pieces.append(op[last:s])
    last = e
    if n not in close:
        pieces.append(noted.get(n, op[s:e]))
pieces.append(op[last:])


def row(m: re.Match) -> str:
    """One index row, repointed if its issue was closed or noted."""
    n = m.group(1)
    if n in close:
        return f"| {n} | {close[n][0]} |{m.group(3)}| docs/OPEN-closed.md |"
    if n in note:
        return f"| {n} | {note[n][0]} |{m.group(3)}| OPEN.md |"
    return m.group(0)


op2 = re.sub(r"^\| (\d+[a-z]?) \| (\S+) \|([^|]*)\| OPEN\.md \|$", row, "".join(pieces), flags=re.M)

out = [cl[:min(s for s, _ in csec.values())]]
for n in sorted(list(csec) + list(close), key=order):
    if n in close:
        out.append(moved[n] + "\n")
    else:
        s, e = csec[n]
        out.append(cl[s:e] if cl[s:e].endswith("\n\n") else cl[s:e].rstrip("\n") + "\n\n")
cl2 = "".join(out).rstrip("\n") + "\n"

print(f"open {len(sec)} -> {len(sections(op2))} · closed {len(csec)} -> {len(sections(cl2))} · "
      f"noted {len(note)}")
if "--dry-run" in sys.argv:
    print("dry run: nothing written")
    sys.exit(0)
OPEN.write_text(op2, encoding="utf-8")
CLOSED.write_text(cl2, encoding="utf-8")
