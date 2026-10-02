---
name: manual-chapter
description: Write or update a chapter of the owner's manual for a command — the Spanish chapter in AlgoData/manual-fuentes from the template, screenshots of the command's REAL output, its family in tools/manual.py, and the rebuilt PDF. Use when a task adds or changes a command (rule 8), when checks.py reports «no manual chapter», or when the owner asks to document something in the manual.
---

# /manual-chapter

The owner reads only the PDFs of `docs/manual/`. Sources and screenshots live in the data root,
`AlgoData/manual-fuentes/` (`core.paths.MANUAL_SRC`) — never a `.md` or an image in `docs/manual/`.

1. **Number and family.** `ls ~/Desktop/AlgoData/manual-fuentes | tail -5` gives the next `NN`;
   `sed -n 27,80p tools/manual.py` shows `FAMILIES`. Which PDF it belongs in is not obvious →
   ask the owner (rule 11). A changed command edits its existing chapter: `grep -l '<module>'
   ~/Desktop/AlgoData/manual-fuentes/*.md`.
2. **Write `NN-<name>.md` in Spanish** from `_PLANTILLA.md` (read it: the sections marked
   *obligatoria* cannot be dropped). Written by someone who knows for someone who does not; the
   command appears by its path or its `python3 -m` dotted form, which is what `checks.py` looks for.
3. **Screenshots are real output, never typed by hand.** Run the command, keep what it printed,
   render it:

   ```bash
   S=<session scratchpad>
   (echo '$ python3 -m x.y.z --arg'; python3 -m x.y.z --arg 2>&1 | sed -n 1,34p) > $S/out.txt
   python3 .claude/skills/manual-chapter/termshot.py $S/out.txt \
       ~/Desktop/AlgoData/manual-fuentes/assets/NN-<name>.png [columns, default 110]
   ```

   A command that starts SQX or burns CPU is not run for a screenshot: use the output the task
   already produced. A window view is shot with `/ui-shot`. Reference it as
   `![…](assets/NN-<name>.png)`.
4. **Register:** the stem in its family in `tools/manual.py`, and a row in
   `manual-fuentes/README.md`.
5. **Build and check:**

   ```bash
   python3 tools/manual.py && python3 tools/checks.py
   ```

   `manual.py` rebuilds only the PDF whose chapters changed and fails on a chapter in no family.
   The changed files of the task then include `docs/manual/<family>.pdf` and `tools/manual.py`.
