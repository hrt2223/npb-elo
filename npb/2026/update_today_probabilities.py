from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import pandas as pd

from elo import HOME_ADVANTAGE, INITIAL_RATING, expected_score


YEAR = 2026
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_RANKING_CSV = BASE_DIR / "output" / "elo_final_ranking.csv"
DEFAULT_OUTPUT_CSV = BASE_DIR / "output" / "today_probabilities.csv"
MONTH_URL = "https://npb.jp/games/{year}/schedule_{month:02d}_detail.html"
JST = ZoneInfo("Asia/Tokyo")

TEAMS = {
    "阪神",
    "DeNA",
    "巨人",
    "中日",
    "広島",
    "ヤクルト",
    "ソフトバンク",
    "日本ハム",
    "オリックス",
    "楽天",
    "西武",
    "ロッテ",
}

CENTRAL = {"阪神", "DeNA", "巨人", "中日", "広島", "ヤクルト"}
PACIFIC = {"ソフトバンク", "日本ハム", "オリックス", "楽天", "西武", "ロッテ"}

DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})")
TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")


@dataclass(frozen=True)
class ScheduleGame:
    date: str
    game_type: str
    home: str
    away: str
    stadium: str
    start_time: str
    status: str


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.items: list[str] = []

    def handle_data(self, data: str) -> None:
        text = re.sub(r"\s+", " ", data).strip()
        if text and text != "\xa0":
            self.items.append(text)


def today_jst() -> str:
    return datetime.now(JST).strftime("%Y-%m-%d")


def fetch_html(url: str, *, timeout: int = 20) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (npb-elo-schedule/1.0)"})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def html_to_tokens(html: str) -> list[str]:
    parser = TextExtractor()
    parser.feed(html)
    return parser.items


def game_type_for(home: str, away: str) -> str:
    if home in CENTRAL and away in CENTRAL:
        return "セ・リーグ"
    if home in PACIFIC and away in PACIFIC:
        return "パ・リーグ"
    return "交流戦"


def parse_month_schedule(tokens: list[str], *, year: int, month: int) -> list[ScheduleGame]:
    games: list[ScheduleGame] = []
    current_date: str | None = None
    i = 0

    while i < len(tokens):
        date_match = DATE_RE.match(tokens[i])
        if date_match:
            parsed_month = int(date_match.group(1))
            day = int(date_match.group(2))
            if parsed_month == month:
                current_date = f"{year}-{parsed_month:02d}-{day:02d}"
            i += 1
            continue

        if current_date and tokens[i] in TEAMS:
            home = tokens[i]
            j = i + 1
            while j < len(tokens) and tokens[j] not in TEAMS and not DATE_RE.match(tokens[j]):
                j += 1

            if j >= len(tokens) or tokens[j] not in TEAMS:
                i += 1
                continue

            away = tokens[j]
            stadium = ""
            start_time = ""
            status = "予定"

            for token in tokens[j + 1 : min(j + 8, len(tokens))]:
                if TIME_RE.match(token):
                    start_time = token
                elif token in {"中止", "試合中", "終了"}:
                    status = token
                elif not stadium and token not in TEAMS and not DATE_RE.match(token):
                    stadium = token

            games.append(
                ScheduleGame(
                    date=current_date,
                    game_type=game_type_for(home, away),
                    home=home,
                    away=away,
                    stadium=stadium,
                    start_time=start_time,
                    status=status,
                )
            )
            i = j + 1
            continue

        i += 1

    return games


def fetch_schedule_for_date(target_date: str, *, year: int = YEAR) -> list[ScheduleGame]:
    month = int(target_date[5:7])
    html = fetch_html(MONTH_URL.format(year=year, month=month))
    games = parse_month_schedule(html_to_tokens(html), year=year, month=month)
    return [game for game in games if game.date == target_date]


def load_ratings(ranking_csv: Path) -> dict[str, float]:
    if not ranking_csv.exists():
        return {}

    ranking_df = pd.read_csv(ranking_csv, encoding="utf-8-sig")
    if ranking_df.empty:
        return {}

    return {
        str(row["team"]): float(row["final_elo"])
        for _, row in ranking_df.iterrows()
        if pd.notna(row.get("team")) and pd.notna(row.get("final_elo"))
    }


def probability_rows(
    games: list[ScheduleGame],
    ratings: dict[str, float],
    *,
    home_advantage: float = HOME_ADVANTAGE,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for game in sorted(games, key=lambda g: (g.start_time, g.home, g.away)):
        home_elo = ratings.get(game.home, INITIAL_RATING)
        away_elo = ratings.get(game.away, INITIAL_RATING)
        home_win_probability = expected_score(home_elo + home_advantage, away_elo)
        away_win_probability = 1.0 - home_win_probability
        rows.append(
            {
                "date": game.date,
                "game_type": game.game_type,
                "home": game.home,
                "away": game.away,
                "stadium": game.stadium,
                "start_time": game.start_time,
                "status": game.status,
                "home_elo": round(home_elo, 1),
                "away_elo": round(away_elo, 1),
                "home_win_probability": round(home_win_probability * 100, 1),
                "away_win_probability": round(away_win_probability * 100, 1),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "date",
        "game_type",
        "home",
        "away",
        "stadium",
        "start_time",
        "status",
        "home_elo",
        "away_elo",
        "home_win_probability",
        "away_win_probability",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update today's NPB schedule and Elo win probabilities.")
    parser.add_argument("--date", default=today_jst(), help="Target date in YYYY-MM-DD. Defaults to today in JST.")
    parser.add_argument("--year", type=int, default=YEAR)
    parser.add_argument("--ranking-csv", type=Path, default=DEFAULT_RANKING_CSV)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--home-advantage", type=float, default=HOME_ADVANTAGE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    games = fetch_schedule_for_date(args.date, year=args.year)
    ratings = load_ratings(args.ranking_csv)
    rows = probability_rows(games, ratings, home_advantage=args.home_advantage)
    write_csv(args.output, rows)

    print(f"Target date: {args.date}")
    print(f"Games: {len(rows)}")
    print(f"CSV: {args.output}")


if __name__ == "__main__":
    main()
