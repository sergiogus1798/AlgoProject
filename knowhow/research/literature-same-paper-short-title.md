---
q: How is a new paper matched to the hand-built literature file, and when is a short title enough?
kw: dedupe papers by title, same paper already in the literature file, short title matches everything, Time series momentum Moskowitz duplicate not detected, edges yaml source free text, arXiv id DOI match
tag: 🔬  date: 2026-10-02  see: verbatim-quote-matching
---
# A paper is matched to the hand-built literature file by arXiv id, DOI, or title — and a short title only with its first author
The 62 hand-built entries carry their source as free text, so a new paper is compared with that text
(`studies/research/literature/dedupe.py::same_paper`). A title of 25 squeezed characters or more is enough on its own; a shorter one
must also find its first author's surname there, or «Time series momentum» would match every paper that cites it — and without the
rule it matched none, because the length guard alone skipped it.

## Evidence
2026-10-02: the first search returned OpenAlex W3124639629, «Time series momentum» (Moskowitz, Ooi, Pedersen), already TR-01..03 of
`edges-2026-10-02.yaml`; with only the ≥ 25-character guard it entered the inbox as new. Now `duplicate`, «same paper as
TR-01-tsmom-12m». `tests/test_literature.py::test_same_paper` holds both sides (same title, another author → new).
