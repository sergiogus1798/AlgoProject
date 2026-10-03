---
q: Which paper search sources (arXiv, OpenAlex, SSRN, Semantic Scholar) answer a plain script?
kw: search papers from Python, arXiv API, OpenAlex API junk results flood plains, SSRN 403, Semantic Scholar 429, paper-search MCP, pyalex, which paper source works without a key, literature scout sources
tag: 🔬  date: 2026-10-02  see: literature-scout-yield, headless-claude-from-cron
---
# arXiv and OpenAlex answer a plain script; SSRN and Semantic Scholar do not; OpenAlex needs a field filter
`studies/research/literature/search.py` uses `httpx` against both, no key, no MCP server, no extra package.
- **arXiv**: `https://export.arxiv.org/api/query` (the `http://` URL answers 301), `(cat:q-fin.TR OR …) AND all:"<words>"`, one request every 3 s.
- **OpenAlex**: `search=<words>` alone returns anything that shares a word («futures» → flood plains, high-entropy alloys). Use
  `filter=title_and_abstract.search:<words>,primary_topic.field.id:20,has_abstract:true` (field 20 = economics, econometrics and finance).
- OpenAlex without a key has a **free daily budget per IP** (1,000 credits, reset at midnight UTC); spent, every request answers 429
  until then. `gather.asked` skips a source that refuses and the run goes on with the others. A free API key lifts it.
- **SSRN** answers 403 to a script (reachable only as OpenAlex abstracts); **Semantic Scholar** 429 without a key; a listed `pdf_url` may return HTML.

## Evidence
2026-10-02, this machine: arXiv http 301 / https 200; OpenAlex 200; `papers.ssrn.com/sol3/papers.cfm?abstract_id=2089463` 403;
`api.semanticscholar.org/graph/v1/paper/search` 429. First search without the field filter: 8 of 20 papers off-topic («Riverine flood
plains», «Plasmonic Films», «Circular futures»); with it, 0 of 21. oa-W2920306588 listed a PDF and gave none.
Same day, 21:00 UTC, after about five searches of 12 queries: `429`, `x-ratelimit-limit: 1000`, `retry-after: 10621`, «free daily
budget shared by everyone on your network's IP address»; the search crashed and registered nothing until `asked` caught it.
