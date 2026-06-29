from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


YEAR = 2026
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_CSV = BASE_DIR / "game_results_jp_2026.csv"
MONTHS = range(3, 12)
NPB_URL = "https://npb.jp/games/{year}/schedule_{month:02d}_detail.html"
TODAY_URL = "https://npb.jp/games/{year}/"

CSV_COLUMNS = [
    "日付",
    "ゲームタイプ",
    "球団",
    "ホーム・ビジター",
    "スコア",
    "対戦球団",
    "GameID",
]

COL_DATE = "日付"
COL_TEAM = "球団"
COL_HOME_AWAY = "ホーム・ビジター"
COL_GAME_ID = "GameID"

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

TEAM_CODES = {
    "阪神": "HT",
    "DeNA": "DB",
    "巨人": "YG",
    "中日": "CD",
    "広島": "HC",
    "ヤクルト": "YS",
    "ソフトバンク": "SH",
    "日本ハム": "F",
    "オリックス": "B",
    "楽天": "E",
    "西武": "L",
    "ロッテ": "M",
}

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

ALL_TEAM_NAMES = TEAMS | set(FULL_TEAM_NAMES)

DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})")
SCORE_RE = re.compile(r"^(\d+)\s*-\s*(\d+)$")
TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")


@dataclass(frozen=True)
class ResultGame:
    date: str
    home: str
    away: str
    home_score: int
    away_score: int
    stadium: str
    start_time: str
    game_id: str


class TextExtractor(HTMLParser):
    def __init__(self, *, include_image_alt: bool = False) -> None:
        super().__init__(convert_charrefs=True)
        self.include_image_alt = include_image_alt
        self.items: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self.include_image_alt or tag != "img":
            return

        alt = dict(attrs).get("alt")
        if alt:
            text = re.sub(r"\s+", " ", alt).strip()
            if text:
                self.items.append(text)

    def handle_data(self, data: str) -> None:
        text = re.sub(r"\s+", " ", data).strip()
        if text:
            self.items.append(text)


def fetch_html(url: str, *, timeout: int = 20) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; local-elo-research/1.0)",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def html_to_tokens(html: str, *, include_image_alt: bool = False) -> list[str]:
    parser = TextExtractor()
    parser.include_image_alt = include_image_alt
    parser.feed(html)
    return [token for token in parser.items if token]


def normalize_score(token: str) -> str:
    return token.replace("－", "-").replace("ー", "-").replace("―", "-")


def parse_score(tokens: list[str], index: int) -> tuple[int, int, int] | None:
    joined_match = SCORE_RE.match(normalize_score(tokens[index]))
    if joined_match:
        return int(joined_match.group(1)), int(joined_match.group(2)), index + 1

    if index + 2 >= len(tokens):
        return None

    if tokens[index].isdigit() and normalize_score(tokens[index + 1]) == "-" and tokens[index + 2].isdigit():
        return int(tokens[index]), int(tokens[index + 2]), index + 3

    return None


def make_game_id(date: str, home: str, away: str, same_day_index: int) -> str:
    compact_date = date.replace("-", "")
    home_code = TEAM_CODES.get(home, home)
    away_code = TEAM_CODES.get(away, away)
    return f"NPB{compact_date}{home_code}{away_code}{same_day_index:02d}"


def normalize_team(name: str) -> str:
    return FULL_TEAM_NAMES.get(name, name)


def is_finished_game_context(tokens: list[str], start: int) -> bool:
    context = tokens[start : min(start + 8, len(tokens))]
    return any(token.startswith(("勝：", "敗：", "分：")) for token in context)


def parse_month(tokens: list[str], *, year: int, month: int) -> list[ResultGame]:
    games: list[ResultGame] = []
    current_date: str | None = None
    games_by_date: dict[str, int] = {}
    i = 0

    while i < len(tokens):
        date_match = DATE_RE.match(tokens[i])
        if date_match:
            parsed_month = int(date_match.group(1))
            day = int(date_match.group(2))
            if parsed_month == month:
                current_date = f"{year}-{parsed_month:02d}-{day:02d}"
                games_by_date.setdefault(current_date, 0)
            i += 1
            continue

        if current_date and tokens[i] in TEAMS and i + 4 < len(tokens):
            home = tokens[i]
            score = parse_score(tokens, i + 1)

            if score:
                home_score, away_score, away_index = score
                away = tokens[away_index] if away_index < len(tokens) else ""

                if away not in TEAMS:
                    i += 1
                    continue

                stadium_index = away_index + 1
                start_time_index = away_index + 2
                if start_time_index >= len(tokens):
                    i += 1
                    continue

                if not is_finished_game_context(tokens, start_time_index + 1):
                    i += 1
                    continue

                stadium = tokens[stadium_index]
                start_time = tokens[start_time_index] if TIME_RE.match(tokens[start_time_index]) else ""
                games_by_date[current_date] += 1
                games.append(
                    ResultGame(
                        date=current_date,
                        home=home,
                        away=away,
                        home_score=home_score,
                        away_score=away_score,
                        stadium=stadium,
                        start_time=start_time,
                        game_id=make_game_id(current_date, home, away, games_by_date[current_date]),
                    )
                )
                i = start_time_index + 1
                continue

        i += 1

    return games


def find_index(tokens: list[str], value: str, *, start: int = 0) -> int:
    try:
        return tokens.index(value, start)
    except ValueError:
        return -1


def find_startswith(tokens: list[str], prefix: str, *, start: int = 0) -> int:
    for index in range(start, len(tokens)):
        if tokens[index].startswith(prefix):
            return index
    return -1


def parse_japanese_month_day(token: str, *, year: int) -> str | None:
    match = re.match(r"^(\d{1,2})月(\d{1,2})日", token)
    if not match:
        return None
    return f"{year}-{int(match.group(1)):02d}-{int(match.group(2)):02d}"


def parse_today_scoreboard(tokens: list[str]) -> tuple[str | None, list[tuple[int, int, str, bool]]]:
    start = find_index(tokens, "試合速報")
    if start < 0:
        return None, []

    date = None
    i = start + 1
    while i < len(tokens):
        date = parse_japanese_month_day(tokens[i], year=YEAR)
        if date:
            break
        i += 1

    end = find_index(tokens, "2026年 勝敗表", start=i)
    if end < 0:
        end = len(tokens)

    scores: list[tuple[int, int, str, bool]] = []
    while i + 3 < end:
        parsed = parse_score(tokens, i)
        if not parsed:
            i += 1
            continue

        home_score, away_score, next_index = parsed
        status_index = next_index
        if status_index < end and normalize_team(tokens[status_index]) in TEAMS:
            status_index += 1
        status = tokens[status_index] if status_index < end else ""
        finished = "試合終了" in status
        scores.append((home_score, away_score, status, finished))
        i = status_index + 1

    return date, scores


def parse_today_schedule(tokens: list[str], *, date_text: str) -> list[tuple[str, str, str, str]]:
    start = find_startswith(tokens, date_text)
    if start < 0:
        return []

    # The date appears once in the速報 section and once in the schedule section.
    second_start = find_startswith(tokens, date_text, start=start + 1)
    if second_start >= 0:
        start = second_start

    schedule: list[tuple[str, str, str, str]] = []
    i = start + 1
    while i + 3 < len(tokens):
        if parse_japanese_month_day(tokens[i], year=YEAR):
            break

        home = normalize_team(tokens[i])
        start_time = tokens[i + 1]
        away = normalize_team(tokens[i + 2])
        stadium = tokens[i + 3]

        if home in TEAMS and away in TEAMS and TIME_RE.match(start_time):
            schedule.append((home, away, stadium, start_time))
            i += 4
            continue

        i += 1

    return schedule


def parse_today_page(tokens: list[str], *, year: int = YEAR) -> list[ResultGame]:
    date, scores = parse_today_scoreboard(tokens)
    if not date:
        return []

    month = int(date[5:7])
    day = int(date[8:10])
    date_text = f"{month}月{day}日"
    schedule = parse_today_schedule(tokens, date_text=date_text)

    games: list[ResultGame] = []
    for index, ((home, away, stadium, start_time), score) in enumerate(zip(schedule, scores), start=1):
        home_score, away_score, _status, finished = score
        if not finished:
            continue

        games.append(
            ResultGame(
                date=date,
                home=home,
                away=away,
                home_score=home_score,
                away_score=away_score,
                stadium=stadium,
                start_time=start_time,
                game_id=make_game_id(date, home, away, index),
            )
        )

    return games


def fetch_games(*, year: int = YEAR, months=MONTHS) -> list[ResultGame]:
    games: list[ResultGame] = []
    for month in months:
        url = NPB_URL.format(year=year, month=month)
        try:
            html = fetch_html(url)
        except (HTTPError, URLError) as exc:
            print(f"Skipped {url}: {exc}")
            continue

        tokens = html_to_tokens(html)
        games.extend(parse_month(tokens, year=year, month=month))

    today_url = TODAY_URL.format(year=year)
    try:
        today_html = fetch_html(today_url)
        today_tokens = html_to_tokens(today_html, include_image_alt=True)
        games.extend(parse_today_page(today_tokens, year=year))
    except (HTTPError, URLError) as exc:
        print(f"Skipped {today_url}: {exc}")

    deduped = {(game.date, game.home, game.away, game.stadium): game for game in games}
    return sorted(deduped.values(), key=lambda game: (game.date, game.start_time, game.game_id))


def fetch_today_games(*, year: int = YEAR) -> list[ResultGame]:
    today_url = TODAY_URL.format(year=year)
    html = fetch_html(today_url)
    tokens = html_to_tokens(html, include_image_alt=True)
    return parse_today_page(tokens, year=year)


def game_to_rows(game: ResultGame) -> list[dict[str, object]]:
    return [
        {
            "日付": game.date,
            "ゲームタイプ": "公式戦",
            "球団": game.home,
            "ホーム・ビジター": "ホーム",
            "スコア": game.home_score,
            "対戦球団": game.away,
            "GameID": game.game_id,
        },
        {
            "日付": game.date,
            "ゲームタイプ": "公式戦",
            "球団": game.away,
            "ホーム・ビジター": "ビジター",
            "スコア": game.away_score,
            "対戦球団": game.home,
            "GameID": game.game_id,
        },
    ]


def write_csv(path: Path, games: list[ResultGame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [row for game in games for row in game_to_rows(game)]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def write_csv_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(
        rows,
        key=lambda row: (
            str(row.get(COL_DATE, "")),
            str(row.get(COL_GAME_ID, "")),
            0 if str(row.get(COL_HOME_AWAY, "")) == "ホーム" else 1,
        ),
    )
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def merge_rows(existing_rows: list[dict[str, object]], new_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    merged: dict[tuple[str, str, str], dict[str, object]] = {}
    for row in existing_rows + new_rows:
        key = (
            str(row.get(COL_GAME_ID, "")),
            str(row.get(COL_TEAM, "")),
            str(row.get(COL_HOME_AWAY, "")),
        )
        merged[key] = row
    return list(merged.values())


def count_games_from_rows(rows: list[dict[str, object]]) -> int:
    return len({str(row.get(COL_GAME_ID, "")) for row in rows if row.get(COL_GAME_ID)})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch completed 2026 NPB results into CSV.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--year", type=int, default=YEAR)
    parser.add_argument("--month", type=int, action="append", help="Fetch only this month. Can be repeated.")
    parser.add_argument("--today-only", action="store_true", help="Fetch only the current scoreboard page.")
    parser.add_argument("--merge-existing", action="store_true", help="Append fetched games to the existing CSV.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.today_only:
        games = fetch_today_games(year=args.year)
    else:
        months = args.month if args.month else MONTHS
        games = fetch_games(year=args.year, months=months)

    fetched_rows = [row for game in games for row in game_to_rows(game)]
    if args.merge_existing:
        existing_rows = read_csv_rows(args.output)
        merged_rows = merge_rows(existing_rows, fetched_rows)
        write_csv_rows(args.output, merged_rows)
        print(f"Fetched completed games: {len(games)}")
        print(f"Total games in CSV: {count_games_from_rows(merged_rows)}")
    else:
        write_csv(args.output, games)
        print(f"Fetched completed games: {len(games)}")

    print(f"CSV: {args.output}")


if __name__ == "__main__":
    main()
