"""Fetch public contribution data — no token required.

Usage: python scripts/fetch_contributions.py
Reads:  https://github.com/users/<username>/contributions
Writes: data/contributions.json
"""

import calendar
import datetime as dt
import json
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "ThomasBonnefoy"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"

URL = f"https://github.com/users/{USERNAME}/contributions"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; profile-readme/1.0)"
}

LEVEL_MAP = {
    "ContributionCalendarDay-l0": 0,
    "ContributionCalendarDay-l1": 1,
    "ContributionCalendarDay-l2": 2,
    "ContributionCalendarDay-l3": 3,
    "ContributionCalendarDay-l4": 4,
}


def parse_iso(date_str: str) -> dt.date:
    return dt.date.fromisoformat(date_str)


def main() -> None:
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    days: list[dict] = []
    for rect in soup.select("td[data-date]"):
        date_str = rect.get("data-date")
        if not date_str:
            continue
        level = 0
        tooltips = rect.get("data-level")
        if tooltips is not None:
            try:
                level = int(tooltips)
            except ValueError:
                level = 0
        else:
            cls = " ".join(rect.get("class", []))
            for key, val in LEVEL_MAP.items():
                if key in cls:
                    level = val
        # data-count fallback
        count_str = rect.get("data-count")
        count = int(count_str) if count_str and count_str.isdigit() else None
        days.append(
            {
                "date": date_str,
                "level": level,
                "count": count,
            }
        )

    if not days:
        print("No contribution cells found — check the username or page HTML.", file=sys.stderr)
        sys.exit(1)

    days.sort(key=lambda d: d["date"])

    # Derived stats
    today = dt.date.today()
    streak = 0
    longest = 0
    best_count = 0
    best_date = None
    monthly: dict[str, int] = {}

    # Current streak (walk backwards from today or last day)
    last_day = parse_iso(days[-1]["date"])
    cursor = last_day
    idx = {parse_iso(d["date"]): d for d in days}
    while cursor in idx and (idx[cursor]["count"] or idx[cursor]["level"]) > 0:
        streak += 1
        cursor -= dt.timedelta(days=1)

    # Longest streak + best day + monthly totals
    run = 0
    for d in days:
        active = (d["count"] or 0) > 0 if d["count"] is not None else d["level"] > 0
        if active:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
        c = d["count"] if d["count"] is not None else 0
        if c > best_count:
            best_count = c
            best_date = d["date"]
        month = d["date"][:7]
        monthly[month] = monthly.get(month, 0) + c

    year_total = sum(
        d["count"] or 0 for d in days if d["count"] is not None
    )
    if year_total == 0:
        year_total = sum(d["level"] for d in days)

    payload = {
        "username": USERNAME,
        "fetched": dt.datetime.now(dt.timezone.utc).isoformat(),
        "year_total": year_total,
        "current_streak": streak,
        "longest_streak": longest,
        "best_day": {"date": best_date, "count": best_count},
        "monthly": monthly,
        "days": days,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({len(days)} days, total={year_total})")


if __name__ == "__main__":
    main()
