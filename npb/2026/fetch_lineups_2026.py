from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import pandas as pd


YEAR = 2026
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SCHEDULE_CSV = BASE_DIR / "output" / "today_probabilities.csv"
DEFAULT_OUTPUT_CSV = BASE_DIR / "output" / "today_lineups.csv"
TODAY_URL = "https://npb.jp/games/{year}/"
MONTH_URL = "https://npb.jp/games/{year}/schedule_{month:02d}_detail.html"
JST = ZoneInfo("Asia/Tokyo")

FULL_TEAM_NAMES = {
    "阪神タイガース": "阪神",
    "横浜DeNAベイスターズ": "DeNA",
    "読売ジャイアンツ": "巨人",
    "中日ドラゴンズ": "中日",
    "広島東洋カープ": "広島",
    "東京ヤクルトスワローズ": "ヤクルト",
    "福岡ソフトバンクホークス": "ソフトバンク",
    "北海道日本ハムファイターズ": "日本ハム",
    "オリックス・バファローズ": "オリックス",
    "東北楽天ゴールデンイーグルス": "楽天",
    "埼玉西武ライオンズ": "西武",
    "千葉ロッテマリーンズ": "ロッテ",
}

FIELDNAMES = [
    "date",
    "game_type",
    "game_key",
    "home",
    "away",
    "team",
    "home_away",
    "batting_order",
    "position",
    "player_name",
    "source_url",
    "fetched_at",
    "status",
]


@dataclass(frozen=True)
class ScheduleGame:
    date: str
    game_type: str
    home: str
    away: str
    start_time: str

    @property
    def key(self) -> str:
        return game_key(self.date, self.home, self.away)


class LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.hrefs.append(href)


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_cell = False
        self.cell_parts: list[str] = []
        self.row: list[str] | None = None
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.row = []
        elif tag in {"td", "th"} and self.row is not None:
            self.in_cell = True
            self.cell_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            text = re.sub(r"\s+", " ", data).strip()
            if text:
                self.cell_parts.append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.in_cell and self.row is not None:
            self.row.append(" ".join(self.cell_parts).strip())
            self.in_cell = False
        elif tag == "tr" and self.row is not None:
            if any(cell for cell in self.row):
                self.rows.append(self.row)
            self.row = None


def now_jst() -> datetime:
    return datetime.now(JST)


def today_jst() -> str:
    return now_jst().strftime("%Y-%m-%d")


def fetch_html(url: str, *, timeout: int = 20) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (npb-elo-lineups/1.0)"})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def game_key(date: str, home: str, away: str) -> str:
    return f"{date}_{home}_{away}"


def read_schedule(path: Path, *, target_date: str) -> list[ScheduleGame]:
    if not path.exists():
        return []

    df = pd.read_csv(path, encoding="utf-8-sig")
    if df.empty:
        return []

    df = df[df["date"].astype(str) == target_date]
    games = []
    for _, row in df.iterrows():
        games.append(
            ScheduleGame(
                date=str(row["date"]),
                game_type=str(row.get("game_type", "")),
                home=str(row["home"]),
                away=str(row["away"]),
                start_time=str(row.get("start_time", "")),
            )
        )
    return games


def is_in_fetch_window(game: ScheduleGame, *, current_time: datetime, minutes_before: int) -> bool:
    if not game.start_time:
        return True

    try:
        hour, minute = [int(part) for part in game.start_time.split(":", 1)]
    except ValueError:
        return True

    start_at = datetime.strptime(game.date, "%Y-%m-%d").replace(
        hour=hour,
        minute=minute,
        tzinfo=JST,
    )
    return current_time >= start_at - timedelta(minutes=minutes_before)


def discover_score_urls(*, year: int, target_date: str) -> list[str]:
    urls: list[str] = []
    sources = [TODAY_URL.format(year=year)]
    month = int(target_date[5:7])
    sources.append(MONTH_URL.format(year=year, month=month))
    pattern = re.compile(rf"/scores/{year}/\d{{4}}/[^\"'#?]+/")

    for source_url in sources:
        try:
            html = fetch_html(source_url)
        except (HTTPError, URLError, TimeoutError) as exc:
            print(f"Skipped score URL source {source_url}: {exc}")
            continue

        parser = LinkExtractor()
        parser.feed(html)
        href_candidates = parser.hrefs + pattern.findall(html)
        for href in href_candidates:
            absolute = urljoin(source_url, href)
            if f"/scores/{year}/" not in absolute:
                continue
            if "/box.html" in absolute or "/playbyplay.html" in absolute or "/roster.html" in absolute:
                continue
            base = absolute.split("#", 1)[0].split("?", 1)[0].rstrip("/") + "/"
            if target_date[5:7] + target_date[8:10] not in base:
                continue
            if base not in urls:
                urls.append(base)

    return urls


def parse_score_teams(rows: list[list[str]]) -> list[str]:
    teams: list[str] = []
    for row in rows:
        if not row:
            continue
        for full_name, short_name in FULL_TEAM_NAMES.items():
            if full_name in row[0] and short_name not in teams:
                teams.append(short_name)
                break
        if len(teams) >= 2:
            return teams
    return teams


def starter_position(value: str) -> str:
    match = re.match(r"^\(([^)]+)\)", value)
    if match:
        return match.group(1)
    return value.strip("()")


def parse_starter_rows(html_text: str, *, home: str, away: str, source_url: str, game: ScheduleGame) -> list[dict[str, object]]:
    parser = TableParser()
    parser.feed(html_text)
    score_teams = parse_score_teams(parser.rows)
    if len(score_teams) < 2:
        return []

    lineup_rows: list[dict[str, object]] = []
    team_index = -1
    for row in parser.rows:
        if len(row) >= 3 and row[1] == "守備" and row[2] == "選手":
            team_index += 1
            continue

        if team_index < 0 or team_index >= len(score_teams):
            continue
        if len(row) < 3 or not row[0].isdigit():
            continue

        batting_order = int(row[0])
        if not 1 <= batting_order <= 9:
            continue

        team = score_teams[team_index]
        lineup_rows.append(
            {
                "date": game.date,
                "game_type": game.game_type,
                "game_key": game.key,
                "home": home,
                "away": away,
                "team": team,
                "home_away": "home" if team == home else "away",
                "batting_order": batting_order,
                "position": starter_position(row[1]),
                "player_name": row[2],
                "source_url": source_url,
                "fetched_at": now_jst().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "available",
            }
        )

    teams_found = {str(row["team"]) for row in lineup_rows}
    if home not in teams_found or away not in teams_found:
        return []

    return sorted(lineup_rows, key=lambda row: (str(row["home_away"]) != "away", int(row["batting_order"])))


def fetch_game_lineups(game: ScheduleGame, score_urls: list[str]) -> list[dict[str, object]]:
    for base_url in score_urls:
        box_url = urljoin(base_url, "box.html")
        try:
            html_text = fetch_html(box_url)
        except (HTTPError, URLError, TimeoutError):
            continue

        rows = parse_starter_rows(html_text, home=game.home, away=game.away, source_url=box_url, game=game)
        if rows:
            return rows

    return []


def read_existing_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return [dict(row) for row in csv.DictReader(f)]


def has_complete_lineup(rows: list[dict[str, str]], game: ScheduleGame) -> bool:
    game_rows = [row for row in rows if row.get("game_key") == game.key and row.get("status") == "available"]
    return len(game_rows) >= 18


def merge_rows(existing_rows: list[dict[str, str]], new_rows: list[dict[str, object]], *, refresh: bool) -> list[dict[str, object]]:
    merged: dict[tuple[str, str, str], dict[str, object]] = {}
    for row in existing_rows:
        key = (str(row.get("game_key", "")), str(row.get("team", "")), str(row.get("batting_order", "")))
        merged[key] = row

    for row in new_rows:
        key = (str(row.get("game_key", "")), str(row.get("team", "")), str(row.get("batting_order", "")))
        if refresh or key not in merged:
            merged[key] = row

    return sorted(
        merged.values(),
        key=lambda row: (
            str(row.get("date", "")),
            str(row.get("game_key", "")),
            0 if str(row.get("home_away", "")) == "away" else 1,
            int(row.get("batting_order") or 0),
        ),
    )


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch today's confirmed NPB starting lineups.")
    parser.add_argument("--date", default=today_jst(), help="Target date in YYYY-MM-DD. Defaults to today in JST.")
    parser.add_argument("--year", type=int, default=YEAR)
    parser.add_argument("--schedule-csv", type=Path, default=DEFAULT_SCHEDULE_CSV)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--minutes-before", type=int, default=30)
    parser.add_argument("--force", action="store_true", help="Ignore the start-time window.")
    parser.add_argument("--refresh", action="store_true", help="Overwrite existing lineup rows for the same game/team/order.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    current_time = now_jst()
    schedule = read_schedule(args.schedule_csv, target_date=args.date)
    existing_rows = read_existing_rows(args.output)
    score_urls = discover_score_urls(year=args.year, target_date=args.date)

    fetched_rows: list[dict[str, object]] = []
    skipped_before_window = 0
    skipped_existing = 0
    not_announced = 0

    for game in schedule:
        if not args.force and not is_in_fetch_window(game, current_time=current_time, minutes_before=args.minutes_before):
            skipped_before_window += 1
            continue
        if not args.refresh and has_complete_lineup(existing_rows, game):
            skipped_existing += 1
            continue

        rows = fetch_game_lineups(game, score_urls)
        if rows:
            fetched_rows.extend(rows)
        else:
            not_announced += 1

    merged_rows = merge_rows(existing_rows, fetched_rows, refresh=args.refresh)
    write_rows(args.output, merged_rows)

    print(f"Target date: {args.date}")
    print(f"Scheduled games: {len(schedule)}")
    print(f"Score URLs discovered: {len(score_urls)}")
    print(f"Fetched lineup games: {len({row['game_key'] for row in fetched_rows})}")
    print(f"Skipped before window: {skipped_before_window}")
    print(f"Skipped existing: {skipped_existing}")
    print(f"Not announced or unavailable: {not_announced}")
    print(f"CSV: {args.output}")


if __name__ == "__main__":
    main()
