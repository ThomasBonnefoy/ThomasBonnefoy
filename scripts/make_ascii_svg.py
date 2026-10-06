"""Convert a prepped grayscale photo into a self-typing monochrome ASCII SVG.

Usage: python scripts/make_ascii_svg.py

Requires source-prepped.png (from prep_photo.py).
Writes: <username>-ascii.svg
"""

import os
import random
from pathlib import Path

from PIL import Image

RAMP = ".`:-=+*cs#%@"  # bright (sparse) -> dark (dense)
CHAR_W = 9
CHAR_H = 16
FONT_SIZE = 13
GRID_W = 100
GRID_H = 53
FILL = "#8b949e"
DELAY_MS = 40
STAGGER_MS = 45
TYPE_DURATION_MS = 180

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "ascii-art.svg"


def brightness_to_glyph(v: float) -> str:
    idx = int((v / 255.0) * (len(RAMP) - 1))
    idx = max(0, min(idx, len(RAMP) - 1))
    return RAMP[idx]


def image_to_rows(img: Image.Image, cols: int, rows: int) -> list[list[str]]:
    img = img.convert("L").resize((cols, rows), Image.LANCZOS)
    pixels = img.load()
    grid: list[list[str]] = []
    for y in range(rows):
        line = []
        for x in range(cols):
            line.append(brightness_to_glyph(pixels[x, y]))
        grid.append(line)
    return grid


def svg_document(rows: list[list[str]], total_w: int, total_h: int) -> str:
    rand = random.Random(42)
    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{total_w}" height="{total_h}" '
        f'viewBox="0 0 {total_w} {total_h}">'
    )
    parts.append(
        f'<rect width="{total_w}" height="{total_h}" fill="none"/>'
    )
    parts.append(
        f'<text font-family="ui-monospace, SFMono-Regular, '
        f'"Menlo, Consolas, monospace" font-size="{FONT_SIZE}" '
        f'fill="{FILL}" xml:space="preserve">'
    )

    for y, line in enumerate(rows):
        text = "".join(line)
        if text.strip() == "":
            continue
        escaped = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        row_h = total_h / len(rows)
        x = 0
        baseline = round((y + 0.8) * row_h, 1)
        clip_id = f"row{y}"
        wipe_w = total_w
        dur = TYPE_DURATION_MS / 1000
        begin = (DELAY_MS / 1000) + (y * STAGGER_MS / 1000)
        rand_val = rand.uniform(0.9, 1.1)
        dur *= rand_val
        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(
            f'<rect x="0" y="{round(y * row_h, 1)}" '
            f'width="0" height="{round(row_h, 1)}">'
            f'<animate attributeName="width" from="0" to="{wipe_w}" '
            f'dur="{dur:.3f}s" begin="{begin:.3f}s" '
            f'fill="freeze"/>'
            f"</rect>"
        )
        parts.append("</clipPath>")
        parts.append(f'<text x="{x}" y="{baseline}" clip-path="url(#{clip_id})">{escaped}</text>')

    parts.append("</text>")
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    if not SRC.exists():
        print(f"Missing {SRC}. Run prep_photo.py first.")
        raise SystemExit(1)

    img = Image.open(SRC)
    rows = image_to_rows(img, GRID_W, GRID_H)
    total_w = GRID_W * CHAR_W
    total_h = GRID_H * CHAR_H

    out_path = os.environ.get("ASCII_OUT")
    out = Path(out_path) if out_path else OUT
    out.write_text(svg_document(rows, total_w, total_h), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
