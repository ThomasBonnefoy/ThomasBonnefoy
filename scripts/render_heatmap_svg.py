"""Render data/contributions.json as an animated contribution heatmap SVG.

Usage: python scripts/render_heatmap_svg.py
Writes: contrib-heatmap.svg
Set STATIC=1 for a frozen frame.
"""

import datetime as dt
import html
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

CELL = 14
GAP = 3
CELL_R = 3
LEFT = 36
TOP = 24
LEGEND_H = 40
CELL_STEP = CELL + GAP

REVEAL_STAGGER = 0.008
REVEAL_DUR = 0.35


def load() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def esc(s: str) -> str:
    return html.escape(str(s))


def render(payload: dict) -> str:
    days = payload["days"]
    by_date = {d["date"]: d for d in days}

    # Build a 53-week x 7-day grid aligned to weeks (Mon-first)
    if not days:
        raise SystemExit("No contribution days to render.")

    end = dt.date.fromisoformat(days[-1]["date"])
    # Find the Monday of the week containing `end`
    start = end - dt.timedelta(days=end.weekday())
    start = start - dt.timedelta(weeks=52)

    weeks: list[list[dt.date | None]] = []
    cursor = start
    while cursor <= end:
        week: list[dt.date | None] = []
        for _ in range(7):
            if cursor <= end:
                week.append(cursor)
            else:
                week.append(None)
            cursor += dt.timedelta(days=1)
        weeks.append(week)

    n_weeks = len(weeks)
    grid_w = n_weeks * CELL_STEP - GAP
    grid_h = 7 * CELL_STEP - GAP
    total_w = LEFT + grid_w + 90  # right padding for legend
    total_h = TOP + grid_h + LEGEND_H + 30

    static = os.environ.get("STATIC") == "1"
    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{total_w}" height="{total_h}" '
        f'viewBox="0 0 {total_w} {total_h}">'
    )
    parts.append(f'<rect width="{total_w}" height="{total_h}" fill="none"/>')

    # Month labels
    prev_month = None
    for wi, week in enumerate(weeks):
        first_day = next((d for d in week if d), None)
        if first_day is None:
            continue
        if prev_month is None or first_day.month != prev_month:
            if first_day.day <= 7:  # only label at start of month
                x = LEFT + wi * CELL_STEP
                parts.append(
                    f'<text x="{x}" y="{TOP - 6}" '
                    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
                    f'font-size="10" fill="#8b949e">{MONTHS[first_day.month - 1]}</text>'
                )
                prev_month = first_day.month

    # Day-of-week labels
    for di, label in enumerate(["Mon", "Wed", "Fri"]):
        y = TOP + (di * 2) * CELL_STEP + CELL - 2
        parts.append(
            f'<text x="0" y="{y}" '
            f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
            f'font-size="10" fill="#8b949e">{label}</text>'
        )

    # Cells
    max_level = max((d["level"] for d in days), default=0)
    reveal_idx = 0
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            if day is None:
                continue
            key = day.isoformat()
            info = by_date.get(key)
            level = info["level"] if info else 0
            color = PALETTE[min(level, len(PALETTE) - 1)]
            x = LEFT + wi * CELL_STEP
            y = TOP + di * CELL_STEP

            if static:
                anim = ""
            else:
                delay = reveal_idx * REVEAL_STAGGER
                # diagonal reveal: row + col
                delay = (wi + di) * 0.012
                anim = (
                    f'<animate attributeName="opacity" from="0" to="1" '
                    f'dur="{REVEAL_DUR}s" begin="{delay:.3f}s" fill="freeze"/>'
                )
            reveal_idx += 1

            count = info["count"] if info and info["count"] is not None else 0
            title = f"{count} contributions on {key}" if count else f"No contributions on {key}"
            parts.append(
                f'<g opacity="{"1" if static else "0"}">{anim}'
                f'<title>{esc(title)}</title>'
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="{CELL_R}" fill="{color}"/>'
                f"</g>"
            )

    # Legend
    lx = LEFT
    ly = TOP + grid_h + 18
    parts.append(
        f'<text x="{lx}" y="{ly + 10}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="11" fill="#8b949e">Less</text>'
    )
    lx += 34
    for i, c in enumerate(PALETTE):
        parts.append(
            f'<rect x="{lx}" y="{ly}" width="{CELL}" height="{CELL}" '
            f'rx="{CELL_R}" fill="{c}"/>'
        )
        lx += CELL_STEP
    parts.append(
        f'<text x="{lx + 4}" y="{ly + 10}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="11" fill="#8b949e">More</text>'
    )

    # Stats footer
    total = payload.get("year_total", 0)
    streak = payload.get("current_streak", 0)
    longest = payload.get("longest_streak", 0)
    footer = (
        f"{total:,} contributions in the last year · "
        f"Longest streak: {longest} days · "
        f"Current streak: {streak} days"
    )
    parts.append(
        f'<text x="{LEFT}" y="{ly + 30}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="12" fill="#c9d1d9">{esc(footer)}</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    if not DATA.exists():
        raise SystemExit(f"Missing {DATA}. Run fetch_contributions.py first.")
    payload = load()
    OUT.write_text(render(payload), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
