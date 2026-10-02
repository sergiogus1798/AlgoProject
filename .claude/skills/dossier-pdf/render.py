"""Render one markdown dossier to a PDF beside it, in the manual's style.

    python3 .claude/skills/dossier-pdf/render.py docs/AgentPDFs/<name>.md
"""
import os
import re
import subprocess
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from core.datapaths import tmp_dir  # noqa: E402
from core.paths import BROWSER  # noqa: E402
from tools.manual import STYLE  # noqa: E402

if len(sys.argv) != 2:
    sys.exit(__doc__)
src = Path(sys.argv[1]).resolve()
text = src.read_text(encoding="utf-8")
body = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"]).convert(text)
title = next((ln[2:].strip() for ln in text.splitlines() if ln.startswith("# ")), src.stem)
# The page sits beside the .md while Chrome prints it, so relative images resolve.
html, pdf = src.with_suffix(".render.html"), src.with_suffix(".pdf")
html.write_text(f"<!doctype html><html lang='es'><head><meta charset='utf-8'><title>{title}</title>"
                f"<style>{STYLE}</style></head><body>{body}</body></html>", encoding="utf-8")
try:
    subprocess.run([str(BROWSER), "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", "--virtual-time-budget=10000",
                    f"--print-to-pdf={pdf}", html.as_uri()],
                   check=True, capture_output=True, env={**os.environ, "TMPDIR": str(tmp_dir())})
finally:
    html.unlink()
pages = len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes()))
print(f"{pdf.name} {pdf.stat().st_size // 1024} KB, {pages} pages")
