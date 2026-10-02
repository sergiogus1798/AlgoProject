---
name: dossier-pdf
description: Turn a dossier written for the owner into the PDF he reads — the Spanish .md in docs/AgentPDFs/, rendered with the manual's style through headless Chrome, and its row in the folder's README. Use when the owner asks for a dossier, a report, an informe or a PDF of a result, or after writing or editing any .md in docs/AgentPDFs/ that he will read.
---

# /dossier-pdf

The owner reads PDFs, not `.md`. The `.md` is the original; the PDF is a product, regenerated
with one command — never re-derive the Chrome call.

1. **Write `docs/AgentPDFs/<tema>-<YYYY-MM-DD>.md`** in Spanish. It ends in a decision with its
   cost next to its gain, every statistic shown is explained in a sentence, charts are big and
   high-contrast (`/dataviz`), and images sit beside it under `docs/AgentPDFs/assets/` only if
   small — heavy figures go to the data root and are referenced by absolute path from
   `core.paths`. A brief for an agent (`prompt-*.md`) needs no PDF: agents read the `.md`.
2. **Render:**

   ```bash
   python3 .claude/skills/dossier-pdf/render.py docs/AgentPDFs/<tema>-<fecha>.md
   ```

   It writes the PDF beside the `.md` with the manual's stylesheet and prints its size and page
   count. Check the page count is sane; to look at a page, delegate it (a Sonnet subagent, one
   document, only the pages needed) — never read a PDF in the main conversation.
3. **Register** its row in `docs/AgentPDFs/README.md` (`file | kind | status`).
4. A dossier acted on, whose facts are in `knowhow/`, is deleted with its PDF — not kept.

The changed files are the `.md`, the `.pdf` and the README.
