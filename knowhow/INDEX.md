# knowhow — index

Hard-won facts about this stack. **Read one file, not all of them.** Pick from the table.

Provenance tags used throughout: 🔬 verified by direct test · 📓 read from logs or files · 🤔 inferred.

| file | read it when you need |
|---|---|
| `01-file-formats.md` | what is inside a `.sqx` or a `project.cfx`, how to identify a strategy, what not to parse |
| `02-databanks.md` | why strategies disappear, what a sync does, memory vs disk |
| `03-driving-sqx.md` | which port/endpoint to use, the `-project` API and its four traps, what MCP cannot do, authoring projects, and the GUI's own HTTP/WebSocket surface a wrapper app would drive |
| `04-export.md` | getting trades, metrics, SPP profiles or bars out — the async traps, the `orderstocsv` schema, IS/OOS views |
| `05-conditions.md` | reading acceptance conditions and `sampleType` correctly |
| `06-locations.md` | where strategies, templates and tools actually live; the full block vocabulary; what the XAUUSD corpus really is |
| `07-practices.md` | working habits that already cost time, research lessons, and what is portable to Windows |
| `08-columns.md` | custom metric columns: where the snippets live, and why their value is frozen into the `.sqx` |
| `09-costs.md` | what SQX can charge and in what unit — commission methods, swap types, where the spread hides |

**Standing rule.** A finding that lives only in a chat transcript is lost when that session ends.
Discovered something non-obvious? Write it into the right file here, in the same task, with its
provenance tag. If it contradicts `CLAUDE.md`, fix `CLAUDE.md` too.

Migrated from `AlgoProject_Old/KNOWHOW.md` on 2026-09-03; paths updated to this tree.
