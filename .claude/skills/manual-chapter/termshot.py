"""Render a text file as a terminal screenshot, for a manual chapter.

    python3 .claude/skills/manual-chapter/termshot.py out.txt shot.png [columns]

Dark background, monospace, lines starting with `$ ` highlighted as the command. Lines longer
than `columns` (default 110) are cut with an ellipsis, so a wide table stays readable in the PDF.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG, FG, CMD = (24, 26, 27), (220, 223, 228), (120, 220, 140)
SIZE, PAD = 16, 18

if len(sys.argv) not in (3, 4):
    sys.exit(__doc__)
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
cols = int(sys.argv[3]) if len(sys.argv) == 4 else 110
lines = [ln.expandtabs(4) for ln in src.read_text(encoding="utf-8").splitlines()] or [
    ""
]
lines = [ln if len(ln) <= cols else ln[: cols - 1] + "…" for ln in lines]

font = ImageFont.truetype("DejaVuSansMono.ttf", SIZE)
width = int(font.getlength("M" * max(len(ln) for ln in lines)))
step = SIZE + 6
img = Image.new("RGB", (width + 2 * PAD, step * len(lines) + 2 * PAD), BG)
draw = ImageDraw.Draw(img)
for i, ln in enumerate(lines):
    draw.text(
        (PAD, PAD + i * step), ln, font=font, fill=CMD if ln.startswith("$ ") else FG
    )
dst.parent.mkdir(parents=True, exist_ok=True)
img.save(dst)
print(f"{dst} {img.width}x{img.height}, {len(lines)} lines")
