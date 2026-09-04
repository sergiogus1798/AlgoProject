#!/usr/bin/env python3
"""Build the whole user manual as one PDF from the markdown pages in docs/manual/."""

import subprocess
import sys
from datetime import date
from pathlib import Path

import markdown

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import BROWSER, MANUAL

HTML = MANUAL / "AlgoProject-Manual.html"
PDF = MANUAL / "AlgoProject-Manual.pdf"

STYLE = """
@page { size: A4; margin: 17mm 15mm 15mm; }
body { font: 10.5pt/1.55 -apple-system, "Segoe UI", Roboto, sans-serif;
       color: #12110f; margin: 0; }
section { break-before: page; }
section:first-of-type, #cover { break-before: auto; }
#cover { height: 232mm; display: flex; flex-direction: column; justify-content: center; }
#cover h1 { font-size: 30pt; margin: 0 0 6px; border: 0; }
#cover p { color: #52514e; margin: 2px 0; }
#cover ol { margin-top: 34px; color: #12110f; }
h1 { font-size: 19pt; margin: 0 0 14px; padding-bottom: 7px;
     border-bottom: 2px solid #2a78d6; }
h2 { font-size: 13pt; margin: 22px 0 7px; break-after: avoid; }
h3 { font-size: 11pt; margin: 16px 0 5px; color: #2a78d6; break-after: avoid; }
p, li { orphans: 3; widows: 3; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 9pt;
       background: #f2f1ee; padding: 1px 4px; border-radius: 3px; }
pre { background: #f7f6f3; border-left: 3px solid #2a78d6; padding: 9px 12px;
      border-radius: 3px; overflow-wrap: break-word; white-space: pre-wrap;
      break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 8.6pt; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9pt;
        break-inside: avoid; }
th, td { border: 1px solid #e4e3df; padding: 4px 7px; text-align: left;
         vertical-align: top; }
th { background: #f7f6f3; font-weight: 600; }
img { max-width: 100%; border: 1px solid #e4e3df; border-radius: 4px;
      margin: 10px 0; break-inside: avoid; }
blockquote { border-left: 3px solid #eb6834; margin: 10px 0; padding: 4px 0 4px 12px;
             color: #52514e; }
a { color: #2a78d6; text-decoration: none; }
"""


def pages() -> list[Path]:
    """The manual's chapters, in reading order.

    Returns:
        Every docs/manual/NN-*.md sorted by name. Files starting with "_" or a letter are
        support material — the template, the pending list, the index — and are not chapters.
    """
    return sorted(p for p in MANUAL.glob("*.md") if p.name[0].isdigit())


def cover(chapters: list[Path]) -> str:
    """The title page.

    Args:
        chapters: The pages that will follow, for the contents list.

    Returns:
        An HTML fragment.
    """
    items = "".join(f"<li>{p.read_text(encoding='utf-8').split(chr(10), 1)[0].lstrip('# ')}</li>"
                    for p in chapters)
    return (f'<div id="cover"><h1>AlgoProject</h1>'
            f'<p>Manual de uso — StrategyQuant X y el análisis en Python</p>'
            f'<p>Generado el {date.today().isoformat()} con <code>tools/manual.py</code>. '
            f'No se edita a mano: se editan las páginas de <code>docs/manual/</code>.</p>'
            f'<ol>{items}</ol></div>')


def render(chapters: list[Path]) -> str:
    """Turn the markdown chapters into one HTML document.

    Args:
        chapters: The pages to include, in order.

    Returns:
        A complete HTML document. Image paths stay relative, so it is written next to the
        assets it references or the pictures come out blank.
    """
    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"])
    body = []
    for page in chapters:
        md.reset()
        body.append(f"<section>{md.convert(page.read_text(encoding='utf-8'))}</section>")
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8">'
            f"<title>AlgoProject — Manual de uso</title><style>{STYLE}</style></head>"
            f"<body>{cover(chapters)}{''.join(body)}</body></html>")


def main() -> None:
    """Write the manual's HTML and print it to a single PDF."""
    chapters = pages()
    HTML.write_text(render(chapters), encoding="utf-8")
    subprocess.run([str(BROWSER), "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", "--virtual-time-budget=10000",
                    f"--print-to-pdf={PDF}", HTML.as_uri()],
                   check=True, capture_output=True)
    print(f"{len(chapters)} chapters -> {PDF} ({PDF.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
