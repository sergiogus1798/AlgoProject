---
q: How is a literature quote matched against the source text (spaces, hyphens, ligatures, minus signs)?
kw: check a quote is verbatim in a PDF's text, pypdf extract_text lost spaces, hyphenated line break, ligature fi, minus sign U+2212, asterisk significance stars, anchors.squeeze, literature validator refuses a quote
tag: 🔬  date: 2026-10-02  see: literature-same-paper-short-title
---
# A quote is matched with spaces, word-break hyphens and ligatures folded — but minus signs and stars kept
`studies/research/literature/anchors.py::squeeze`: NFKD to ASCII, lower case, every space gone, a hyphen kept only before a digit
(a minus sign or a range; any other is a word broken at a line end). U+2212, en and em dashes become `-`, U+2217 becomes `*`.
Dropping every non-alphanumeric character looked harmless and was not: a table row with a sign wrong still matched.
The check proves the quote is in the source at that page — never that the entry's value says no more than the quote.

## Evidence
2026-10-02, first batch: the scout quoted `SPX 0.10% −0.09% 0.20% ** 0.15% …` (p. 6 of oa-W4224305608); under the first `squeeze`
`0.09%` without its minus matched too. After the fix all 5 entries' anchors and the 16 quoted rejections still validate.
`tests/test_literature.py::test_anchors`: a word broken as `pre-\nceding`, `Proﬁts`, a sign dropped, a star dropped.
A fragment of a sentence passes (20 characters minimum): nothing enforces a whole sentence.
