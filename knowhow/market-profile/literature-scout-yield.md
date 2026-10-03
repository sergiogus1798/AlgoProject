---
q: What did the first literature scout run yield and cost per read?
kw: literature scout yield, how many papers give a rule, tokens per paper, cost per entry, abstract only papers useless, papers without PDF, ambiguous rules in papers, first batch 20 papers
tag: 🔬  date: 2026-10-02  see: paper-search-sources, token-spend-is-context-reread
---
# Day one: 97 items read, 24 useful (33 entries); 20 of 33 wait on a question; a read costs 18-30k tokens as one tool-less call
73 rejected: 35 `no_rule`, 8 `clock`, 7 `fundamentals`, 7 `two_legs`, 6 `cross_sectional`, 5 `unreadable`, 5 other.
- Practitioner pages and code collections give a rule more often (10 of 25) than searched papers (14 of 72); an abstract alone
  almost never does (0 of 13), so OpenAlex is asked only for open PDFs. 20 entries wait on the owner, 10 have no measure, 2 measured.
- A too-narrow filter costs entries: re-read under «futures papers are wanted, a model paper's stated benchmark rules count»,
  4 of 9 rejected papers gave 5 entries. A rule filed under another family is the same rule (dedupe ignores the family).
- Cost is context × turns: an agent loop re-reads ~41k tokens per tool use (30-46k per paper); a single-turn call with `--tools ""`,
  own system prompt, no MCP, no skills is ~10k fixed, 18-30k per call with opus. Tokens, never dollars (owner).

## Evidence
`python3 -m studies.research.literature.report`, `--rejections`, `--queue`; `AlgoData/research/literature/runs.jsonl` (runs 140144 opus
one agent 171,568 tok / 20 papers, self-reported; 143154 923,856 / 20; 143808 605,582 / 20, 7 calls; 144518 128,411 / 7, 6 calls, 0 re-read).
Counts by PDF: `papers.jsonl`, `pdf` × `read` × `status`.
