from __future__ import annotations

import argparse
import csv
from datetime import date, datetime
from pathlib import Path
from urllib.error import HTTPError

from update_today_probabilities import (
    BASE_DIR,
    JST,
    MONTH_URL,
    YEAR,
    fetch_html,
    fetch_schedule_for_date,
    html_to_tokens,
    parse_month_schedule,
)


DEFAULT_OUTPUT_CSV = BASE_DIR / "output" / "upcoming_schedule.csv"
CSV_COLUMNS = ["date", "game_type", "home", "away", "stadium", "start_time"]
SCHEDULED_STATUS = "予定"


def today_jst() -> str:
    return datetime.now(JST).strftime("%Y-%m-%d")


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def month_range(start: date, end: date) -> list[tuple[int, int]]:
    months: list[tuple[int, int]] = []
    year = start.year
    month = start.month

    while (year, month) <= (end.year, end.month):
        months.append((year, month))
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

    return months


def fetch_upcoming_schedule(date_from: str, date_to: str, *, year: int = YEAR) -> list[dict[str, str]]:
    start = parse_date(date_from)
    end = parse_date(date_to)
    if end < start:
        raise ValueError("--to must be on or after --from")
    today = parse_date(today_jst())
    if start < today:
        print(f"Clamped --from {start.isoformat()} to today {today.isoformat()}")
        start = today
        if end < start:
            return []

    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str, str, str]] = set()
    try:
        start_date_statuses = {
            (game.date, game.home, game.away): game.status
            for game in fetch_schedule_for_date(start.isoformat(), year=year)
        }
    except HTTPError as exc:
        if exc.code != 404:
            raise
        start_date_statuses = {}

    for page_year, month in month_range(start, end):
        if page_year != year:
            continue

        try:
            html = fetch_html(MONTH_URL.format(year=year, month=month))
        except HTTPError as exc:
            if exc.code == 404:
                print(f"Skipped missing schedule page: {year}-{month:02d}")
                continue
            raise
        games = parse_month_schedule(html_to_tokens(html), year=year, month=month)

        for game in games:
            game_date = parse_date(game.date)
            if game_date < start or game_date > end:
                continue
            status = start_date_statuses.get((game.date, game.home, game.away), game.status)
            if status != SCHEDULED_STATUS:
                continue

            key = (game.date, game.game_type, game.home, game.away, game.stadium, game.start_time)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "date": game.date,
                    "game_type": game.game_type,
                    "home": game.home,
                    "away": game.away,
                    "stadium": game.stadium,
                    "start_time": game.start_time,
                }
            )

    rows.sort(key=lambda row: (row["date"], row["start_time"], row["home"], row["away"]))
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch upcoming scheduled NPB games.")
    parser.add_argument("--from", dest="date_from", default=today_jst())
    parser.add_argument("--to", dest="date_to", default=f"{YEAR}-12-31")
    parser.add_argument("--year", type=int, default=YEAR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_CSV)
    args = parser.parse_args()

    rows = fetch_upcoming_schedule(args.date_from, args.date_to, year=args.year)
    write_csv(args.output, rows)
    print(f"Wrote {len(rows)} upcoming scheduled games to {args.output}")


if __name__ == "__main__":
    main()
