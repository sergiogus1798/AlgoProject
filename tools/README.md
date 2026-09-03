# tools — project maintenance

| file | what it does | run it |
|---|---|---|
| `checks.py` | Verify every mechanical rule in `CODESTYLE.md` and list what breaks them | `python3 tools/checks.py` |
| `depmap.py` | Read the real imports and regenerate `docs/DEPENDENCIES.md` | `python3 tools/depmap.py` |

`sqx-lab/` is a vendored plugin, not project code: four skills that author custom blocks, random
groups, strategy templates and build projects. **Its path must not move** — `~/.claude/skills/sqx-*`
and `~/.claude/sqx_common.py` are symlinks into it, and `/sqx-setup` and `/sqx-doctor` name it
literally. `checks.py` and `depmap.py` skip it.

Run both tools after touching any Python:

```bash
python3 tools/depmap.py && python3 tools/checks.py
```
