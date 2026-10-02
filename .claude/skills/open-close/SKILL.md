---
name: open-close
description: Close issues of OPEN.md or add a dated note to one — move each closed section verbatim to docs/OPEN-closed.md in numeric order, flip its emoji and its index row. Use when the owner says an issue is done, asks to close, archive or update OPEN.md issues, or after a task that resolved one. Replaces the throwaway scratch/close_open*.py scripts.
---

# /open-close

`OPEN.md` keeps what is open; a closed issue lives verbatim in `docs/OPEN-closed.md` with its
number. Fourteen sessions rewrote the same script; it is `close.py` here.

1. **Find the sections** without reading the file: `grep -n '^## <N>' OPEN.md`, read only those.
   Unsure whether an issue is really closed, or only part of it is → ask the owner (rule 11);
   a partly done issue gets a `note`, not a `close`.
2. **Write the spec** as JSON in the session scratchpad:

   ```json
   {"close": {"71": ["🟢", "What was done, how it was verified, where it lives now (file, test, card)."]},
    "note":  {"85": ["🟡", "What changed today and what is still open."]}}
   ```

   Emoji: 🟢 done · ⚪ closed without a fix (won't fix, superseded, owner's decision) · ✅ verified
   live; for a note, the status the issue is left in. The text is English, one paragraph, and names
   the evidence — it is all a later session will read.
3. **Apply and check:**

   ```bash
   python3 .claude/skills/open-close/close.py <spec.json> --dry-run   # counts only
   python3 .claude/skills/open-close/close.py <spec.json>
   python3 tools/checks.py
   ```

   It stamps today's date, refuses an unknown or already-closed number, and prints the open and
   closed section counts — open must drop by exactly the number closed.
4. A fact the issue taught that is not yet a card → `/doc`.
