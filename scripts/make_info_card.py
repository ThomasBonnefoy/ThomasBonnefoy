"""Build a neofetch-style info card as a self-typing SVG.

Usage: python scripts/make_info_card.py
Writes: info-card.svg
Set STATIC=1 for a frozen frame.
"""

import html
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"

W = 490
H = 370
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
TITLE_BG = "#161b22"
TITLE_FG = "#58a6ff"
LABEL_FG = "#7ee787"
VALUE_FG = "#c9d1d9"
DIM_FG = "#8b949e"
BAR_COLORS = ["#f778ba", "#ffa657", "#e3b341", "#7ee787", "#79c0ff", "#d2a8ff"]

ROWS = [
    ("Now", "2nd-yr BUT Informatique — IUT Lyon 1"),
    ("Focus", "Web dev · Linux · Networks · Self-hosting"),
    ("Stack", "C++ · Kotlin · JS/Node · Python · Bash"),
    ("Web", "HTML · CSS · PHP · JavaScript"),
    ("Infra", "Docker · Caddy · Tailscale · systemd"),
    ("Embedded", "ESP32 · Arduino · Qt 6 · Raspberry Pi"),
    ("Tools", "Git · CMake · VS Code · Wireshark"),
    ("Speak", "FR (native) · EN (professional)"),
]


def esc(s: str) -> str:
    return html.escape(s)


def build(static: bool) -> str:
    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
    )
    parts.append(
        f'<rect width="{W}" height="{H}" rx="8" fill="{TITLE_BG}"/>'
    )

    # Title bar
    parts.append(
        f'<text x="16" y="26" font-family="{FONT}" font-size="14" '
        f'fill="{TITLE_FG}">thomas@github:~$ neofetch</text>'
    )
    parts.append(
        f'<line x1="0" y1="40" x2="{W}" y2="40" stroke="#30363d" stroke-width="1"/>'
    )

    row_y = 64
    row_h = 34
    static_mode = os.environ.get("STATIC") == "1" or static

    for i, (label, value) in enumerate(ROWS):
        begin = 0.15 + i * 0.09
        color = BAR_COLORS[i % len(BAR_COLORS)]
        opacity = (
            ' opacity="1"' if static_mode else ""
        )
        anim = "" if static_mode else (
            f'<animate attributeName="opacity" from="0" to="1" '
            f'dur="0.4s" begin="{begin:.2f}s" fill="freeze"/>'
        )
        y = row_y + i * row_h
        parts.append(
            f'<g{opacity}>{anim}'
            f'<text x="20" y="{y}" font-family="{FONT}" font-size="13" '
            f'fill="{LABEL_FG}">{esc(label)}</text>'
            f'<text x="90" y="{y}" font-family="{FONT}" font-size="13" '
            f'fill="{color}">:</text>'
            f'<text x="104" y="{y}" font-family="{FONT}" font-size="13" '
            f'fill="{VALUE_FG}">{esc(value)}</text>'
            f"</g>"
        )

    # Footer bar
    parts.append(
        f'<rect x="20" y="{H - 28}" width="{W - 40}" height="8" rx="4" fill="#21262d"/>'
    )
    for i in range(7):
        bw = (W - 40) // 7
        c = BAR_COLORS[i % len(BAR_COLORS)]
        parts.append(
            f'<rect x="{20 + i * bw}" y="{H - 28}" '
            f'width="{bw - 2}" height="8" rx="4" fill="{c}"/>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    OUT.write_text(build(False), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
