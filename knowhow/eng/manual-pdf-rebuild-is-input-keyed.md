---
q: manual pdf changes every rebuild, docs/manual git churn, chrome print-to-pdf not deterministic, CreationDate ModDate, .rendered.json, force manual rebuild
tag: 🔬  date: 2026-09-29  see:
---
# `tools/manual.py` re-renders a family only when its inputs change
Chrome's `--print-to-pdf` is not byte-stable: `/CreationDate` and `/ModDate` change every run, and on
some runs the image streams too (05, 06, 10 differed after the timestamps were masked). The cover
also printed today's date. So every rebuild rewrote all ten PDFs, and git stores each whole:
477 PDF versions were ~53 MB of a 62 MB `.git`. Now the cover shows its chapters' last change and
each family is keyed on a hash of its HTML plus every picture it shows, kept in
`AlgoData/manual-fuentes/.rendered.json`. Delete that file to force a full rebuild.

## Evidence
2026-09-29: committed vs rebuilt `10-cierre.pdf` → same size, 12 bytes differ, all in the two dates.
Byte comparison after masking dates still rewrote 3 families run to run. With input keys: second
run → all ten "unchanged" in 1.6 s; dropping one key → only that family rendered.
`git rev-list --objects --all -- docs/manual docs/AgentPDFs | git cat-file --batch-check` → 477 blobs.
