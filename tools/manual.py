#!/usr/bin/env python3
"""Build the user manual as one PDF per workflow family, from the markdown in AlgoData.

The owner reads only the PDFs (2026-09-26): docs/manual/ holds nothing else. The chapters and
their screenshots live in MANUAL_SRC, out of the repo; edit a chapter there and rerun this.
"""

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import markdown

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import BROWSER, MANUAL, MANUAL_SRC

# One PDF per family, chapters in reading order. A chapter missing from every family is an error.
FAMILIES = {
    "01-empezar": ("Empezar", [
        "00-empezar", "20-donde-esta-todo", "21-vocabulario", "46-knowhow", "23-skills",
        "10-github"]),
    "02-la-ventana": ("La ventana de escritorio", [
        "35-app-plantillas", "38-app-activos", "48-app-generacion", "44-app-estrategias",
        "45-app-puerta"]),
    "03-datos-costes-y-registro": ("Datos, costes y registro de la búsqueda", [
        "13-barras", "57-calidad-del-feed", "59-spread-real", "25-actualizar-datos", "24-costes", "43-ledger",
        "12-rendimiento"]),
    "04-sqx-plantillas-y-proyectos": ("SQX: bloques, plantillas y proyectos", [
        "40-sqx-lab", "36-taxonomia", "22-plantillas", "28-builder", "47-proyecto-workflow",
        "06-mover-estrategias", "27-curar", "17-pipeline", "55-retirar-proyectos"]),
    "05-cribado-oos": ("Cribado fuera de muestra", [
        "01-analisis-is-oos", "02-filtros", "03-comparar-muestras", "04-decaimiento",
        "29-puerta", "49-snooping"]),
    "06-lecturas": ("Lecturas de una estrategia", [
        "26-nulos", "50-edge-por-coste", "40-forma-del-beneficio", "42-calidad-de-la-entrada",
        "53-mapa-condicional", "51-estructura"]),
    "07-otros-mercados-y-timeframes": ("Otros mercados y otros timeframes", [
        "30-crossmarket", "05-retest-mercados", "39-crossmarket-lote", "31-crosstf"]),
    "08-montecarlo": ("Monte Carlo y MC Retest", [
        "07-montecarlo", "32-mcretest", "11-retest-mc"]),
    "09-optimizacion": ("Parámetros: SPP, variantes, WFC, CSCV y WFM", [
        "33-spp", "08-spp", "09-diccionario-spp", "15-sppultra", "18-variantes",
        "37-wfc-retest", "19-wfc", "25-cscv", "39-nube-de-parametros",
        "52-superficies-mercado", "34-wfm", "09-wfm", "14-walkforwardmatrix"]),
    "10-cierre": ("El cierre: paso 20, exposición y stop para MT5", [
        "56-paso-20", "38-exposicion", "54-atr-calculator"]),
}

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

_LINK = re.compile(r"\]\((\d\d-[a-z0-9-]+)\.md(#[^)]*)?\)")
_MENTION = re.compile(r"(?:docs/manual/)?(\d\d-[a-z0-9-]+)\.md")


def home() -> dict[str, str]:
    """Which PDF each chapter lives in.

    Returns:
        Chapter stem -> family stem.
    """
    return {ch: fam for fam, (_, chapters) in FAMILIES.items() for ch in chapters}


def relink(text: str, where: dict[str, str]) -> str:
    """Point every reference to another chapter at the PDF that now holds it.

    Args:
        text: One chapter's markdown.
        where: The map from home().

    Returns:
        The markdown with `NN-name.md` links and mentions rewritten to `family.pdf`.
    """
    text = _LINK.sub(lambda m: f"]({where.get(m[1], m[1])}.pdf)", text)
    return _MENTION.sub(lambda m: f"{where[m[1]]}.pdf › {m[1]}" if m[1] in where else m[0], text)


def title(page: Path) -> str:
    """A chapter's first heading, without the hashes."""
    return page.read_text(encoding="utf-8").split("\n", 1)[0].lstrip("# ")


def cover(name: str, chapters: list[Path]) -> str:
    """The title page of one family, and on the first one the list of every PDF.

    Args:
        name: The family's title.
        chapters: The pages that follow, for the contents list.

    Returns:
        An HTML fragment.
    """
    items = "".join(f"<li>{title(p)}</li>" for p in chapters)
    rest = "".join(f"<li><b>{fam}.pdf</b> — {t}</li>" for fam, (t, _) in FAMILIES.items())
    index = f"<p style='margin-top:28px'>El manual entero:</p><ul>{rest}</ul>" \
        if chapters and chapters[0].stem == "00-empezar" else ""
    return (f'<div id="cover"><h1>{name}</h1>'
            f'<p>AlgoProject — manual de uso. Generado el {date.today().isoformat()} '
            f'con <code>tools/manual.py</code>.</p><ol>{items}</ol>{index}</div>')


def render(name: str, chapters: list[Path], where: dict[str, str]) -> str:
    """Turn one family's chapters into one HTML document.

    Args:
        name: The family's title.
        chapters: The pages to include, in order.
        where: The map from home(), to relink cross-references.

    Returns:
        A complete HTML document. Image paths stay relative, so it is written next to the
        assets it references or the pictures come out blank.
    """
    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"])
    body = []
    for page in chapters:
        md.reset()
        text = relink(page.read_text(encoding="utf-8"), where)
        body.append(f"<section>{md.convert(text)}</section>")
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8">'
            f"<title>AlgoProject — {name}</title><style>{STYLE}</style></head>"
            f"<body>{cover(name, chapters)}{''.join(body)}</body></html>")


def main() -> None:
    """Write one PDF per family into docs/manual/, from the chapters in MANUAL_SRC."""
    found = {p.stem for p in MANUAL_SRC.glob("*.md") if p.name[0].isdigit()}
    where = home()
    if found - set(where) or set(where) - found:
        raise SystemExit(f"chapters without a family: {sorted(found - set(where))}; "
                         f"families naming a missing chapter: {sorted(set(where) - found)}")
    for fam, (name, stems) in FAMILIES.items():
        html, pdf = MANUAL_SRC / f"{fam}.html", MANUAL / f"{fam}.pdf"
        html.write_text(render(name, [MANUAL_SRC / f"{s}.md" for s in stems], where),
                        encoding="utf-8")
        subprocess.run([str(BROWSER), "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--no-pdf-header-footer", "--virtual-time-budget=10000",
                        f"--print-to-pdf={pdf}", html.as_uri()],
                       check=True, capture_output=True)
        html.unlink()
        print(f"{len(stems):2d} chapters -> {pdf.name} ({pdf.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
