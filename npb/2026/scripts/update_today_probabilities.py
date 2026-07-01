from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass, replace
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import pandas as pd

from elo import (
    HOME_ADVANTAGE,
    INITIAL_RATING,
    K_FACTOR,
    LOGISTIC_BASE,
    LOGISTIC_SCALE,
    expected_score,
    update_ratings,
)


YEAR = 2026
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_RANKING_CSV = BASE_DIR / "output" / "elo_final_ranking.csv"
DEFAULT_OUTPUT_CSV = BASE_DIR / "output" / "today_probabilities.csv"
TODAY_URL = "https://npb.jp/games/{year}/"
MONTH_URL = "https://npb.jp/games/{year}/schedule_{month:02d}_detail.html"
STARTER_URL = "https://npb.jp/announcement/starter/"
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

SCORE_TEAM_CODES = {
    "t": "阪神",
    "db": "DeNA",
    "g": "巨人",
    "d": "中日",
    "c": "広島",
    "s": "ヤクルト",
    "h": "ソフトバンク",
    "f": "日本ハム",
    "b": "オリックス",
    "e": "楽天",
    "l": "西武",
    "m": "ロッテ",
}

DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})")
TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")
SCORE_LINK_RE = re.compile(r'<a\s+[^>]*href="(?P<href>[^"]*/scores/[^"]+)"[^>]*>(?P<body>.*?)</a>', re.DOTALL)
SCORE_HREF_RE = re.compile(r"/scores/(?P<year>\d{4})/(?P<mmdd>\d{4})/(?P<home>[a-z]+)-(?P<away>[a-z]+)-\d+/?")
STARTER_UNIT_RE = re.compile(r'<div class="unit [^"]+">(.*?)</div>\s*</div>', re.DOTALL)
TEAM_STARTER_RE = re.compile(
    r'<div class="team_(left|right)">.*?alt="([^"]+)".*?<span>(.*?)</span>',
    re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")


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


def parse_schedule_probable_starters(tokens: list[str], *, year: int, month: int, target_date: str) -> dict[tuple[str, str], dict[str, str]]:
    starters: dict[tuple[str, str], dict[str, str]] = {}
    current_date: str | None = None
    i = 0

    while i < len(tokens):
        date_match = DATE_RE.match(tokens[i])
        if date_match:
            parsed_month = int(date_match.group(1))
            day = int(date_match.group(2))
            current_date = f"{year}-{parsed_month:02d}-{day:02d}" if parsed_month == month else None
            i += 1
            continue

        if current_date == target_date and tokens[i] in TEAMS:
            home = tokens[i]
            j = i + 1
            while j < len(tokens) and tokens[j] not in TEAMS and not DATE_RE.match(tokens[j]):
                j += 1

            if j >= len(tokens) or tokens[j] not in TEAMS:
                i += 1
                continue

            away = tokens[j]
            starter_tokens = [
                token.removeprefix("先発：").strip()
                for token in tokens[j + 1 : min(j + 12, len(tokens))]
                if token.startswith("先発：")
            ]
            if len(starter_tokens) >= 2:
                starters[(home, away)] = {
                    "home_probable_starter": starter_tokens[0],
                    "away_probable_starter": starter_tokens[1],
                }

            i = j + 1
            continue

        i += 1

    return starters


def score_statuses_from_html(html: str, *, year: int, target_date: str) -> dict[tuple[str, str], str]:
    statuses: dict[tuple[str, str], str] = {}
    mmdd = f"{int(target_date[5:7]):02d}{int(target_date[8:10]):02d}"
    for match in SCORE_LINK_RE.finditer(html):
        href_match = SCORE_HREF_RE.search(match.group("href"))
        if not href_match:
            continue
        if href_match.group("year") != str(year) or href_match.group("mmdd") != mmdd:
            continue

        home = SCORE_TEAM_CODES.get(href_match.group("home"))
        away = SCORE_TEAM_CODES.get(href_match.group("away"))
        if not home or not away:
            continue

        text = re.sub(r"\s+", " ", TAG_RE.sub("", match.group("body"))).strip()
        if "中止" in text:
            statuses[(home, away)] = "中止"
        elif "試合終了" in text:
            statuses[(home, away)] = "終了"
        elif "回" in text:
            statuses[(home, away)] = "試合中"

    return statuses


def apply_score_statuses(games: list[ScheduleGame], statuses: dict[tuple[str, str], str]) -> list[ScheduleGame]:
    if not statuses:
        return games
    return [
        replace(game, status=statuses.get((game.home, game.away), game.status))
        for game in games
    ]


def fetch_schedule_for_date(target_date: str, *, year: int = YEAR) -> list[ScheduleGame]:
    month = int(target_date[5:7])
    html = fetch_html(MONTH_URL.format(year=year, month=month))
    games = parse_month_schedule(html_to_tokens(html), year=year, month=month)
    status_html = html
    try:
        status_html = fetch_html(TODAY_URL.format(year=year))
    except OSError as exc:
        print(f"Skipped score statuses: {exc}")

    statuses = score_statuses_from_html(status_html, year=year, target_date=target_date)
    return apply_score_statuses([game for game in games if game.date == target_date], statuses)


def fetch_schedule_probable_starters(target_date: str, *, year: int = YEAR) -> dict[tuple[str, str], dict[str, str]]:
    month = int(target_date[5:7])
    try:
        html = fetch_html(MONTH_URL.format(year=year, month=month))
    except OSError as exc:
        print(f"Skipped schedule probable starters: {exc}")
        return {}
    return parse_schedule_probable_starters(html_to_tokens(html), year=year, month=month, target_date=target_date)



def clean_html_text(value: str) -> str:
    return re.sub(r"\s+", " ", TAG_RE.sub("", value)).strip()


def normalize_team(name: str) -> str:
    return FULL_TEAM_NAMES.get(name, name)


def parse_starter_page_tokens(tokens: list[str]) -> dict[tuple[str, str], dict[str, str]]:
    team_starters: list[tuple[str, str]] = []
    i = 0
    while i < len(tokens) - 1:
        if tokens[i] in FULL_TEAM_NAMES:
            team = normalize_team(tokens[i])
            player = tokens[i + 1].strip()
            if team in TEAMS and player and player not in FULL_TEAM_NAMES and not player.startswith("（"):
                team_starters.append((team, player.replace("\u3000", " ")))
                i += 2
                continue
        i += 1

    starters: dict[tuple[str, str], dict[str, str]] = {}
    for left, right in zip(team_starters[0::2], team_starters[1::2]):
        home, home_starter = left
        away, away_starter = right
        starters[(home, away)] = {
            "home_probable_starter": home_starter,
            "away_probable_starter": away_starter,
        }

    return starters


def fetch_probable_starters() -> dict[tuple[str, str], dict[str, str]]:
    try:
        html = fetch_html(STARTER_URL)
    except OSError as exc:
        print(f"Skipped probable starters: {exc}")
        return {}

    starters: dict[tuple[str, str], dict[str, str]] = {}
    for unit_match in STARTER_UNIT_RE.finditer(html):
        unit_html = unit_match.group(1)
        teams = TEAM_STARTER_RE.findall(unit_html)
        if len(teams) < 2:
            continue

        parsed: dict[str, tuple[str, str]] = {}
        for side, full_team, player_html in teams[:2]:
            team = normalize_team(clean_html_text(full_team))
            player = clean_html_text(player_html).replace("\u3000", " ")
            if team in TEAMS and player:
                parsed[side] = (team, player)

        if "left" not in parsed or "right" not in parsed:
            continue

        home, home_starter = parsed["left"]
        away, away_starter = parsed["right"]
        starters[(home, away)] = {
            "home_probable_starter": home_starter,
            "away_probable_starter": away_starter,
        }

    for key, value in parse_starter_page_tokens(html_to_tokens(html)).items():
        starters.setdefault(key, value)

    return starters


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


def elo_delta_scenarios(
    home_elo: float,
    away_elo: float,
    *,
    k_factor: float = K_FACTOR,
    home_advantage: float = HOME_ADVANTAGE,
    logistic_base: float = LOGISTIC_BASE,
    logistic_scale: float = LOGISTIC_SCALE,
) -> dict[str, float]:
    scenarios = {
        "home_win": (1, 0),
        "away_win": (0, 1),
        "draw": (0, 0),
    }
    deltas: dict[str, float] = {}
    for key, (home_score, away_score) in scenarios.items():
        new_home, new_away, _, _ = update_ratings(
            home_elo,
            away_elo,
            home_score,
            away_score,
            k_factor=k_factor,
            home_advantage=home_advantage,
            logistic_base=logistic_base,
            logistic_scale=logistic_scale,
        )
        deltas[f"home_delta_if_{key}"] = round(new_home - home_elo, 1)
        deltas[f"away_delta_if_{key}"] = round(new_away - away_elo, 1)
    return deltas


def probability_rows(
    games: list[ScheduleGame],
    ratings: dict[str, float],
    *,
    probable_starters: dict[tuple[str, str], dict[str, str]] | None = None,
    k_factor: float = K_FACTOR,
    home_advantage: float = HOME_ADVANTAGE,
    logistic_base: float = LOGISTIC_BASE,
    logistic_scale: float = LOGISTIC_SCALE,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    probable_starters = probable_starters or {}
    for game in sorted(games, key=lambda g: (g.start_time, g.home, g.away)):
        home_elo = ratings.get(game.home, INITIAL_RATING)
        away_elo = ratings.get(game.away, INITIAL_RATING)
        starters = probable_starters.get((game.home, game.away), {})
        home_win_probability = expected_score(
            home_elo + home_advantage,
            away_elo,
            logistic_base=logistic_base,
            logistic_scale=logistic_scale,
        )
        away_win_probability = 1.0 - home_win_probability
        deltas = elo_delta_scenarios(
            home_elo,
            away_elo,
            k_factor=k_factor,
            home_advantage=home_advantage,
            logistic_base=logistic_base,
            logistic_scale=logistic_scale,
        )
        rows.append(
            {
                "date": game.date,
                "game_type": game.game_type,
                "home": game.home,
                "away": game.away,
                "stadium": game.stadium,
                "start_time": game.start_time,
                "status": game.status,
                "home_probable_starter": starters.get("home_probable_starter", ""),
                "away_probable_starter": starters.get("away_probable_starter", ""),
                "home_elo": round(home_elo, 1),
                "away_elo": round(away_elo, 1),
                "home_win_probability": round(home_win_probability * 100, 1),
                "away_win_probability": round(away_win_probability * 100, 1),
                **deltas,
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
        "home_probable_starter",
        "away_probable_starter",
        "home_elo",
        "away_elo",
        "home_win_probability",
        "away_win_probability",
        "home_delta_if_home_win",
        "away_delta_if_home_win",
        "home_delta_if_away_win",
        "away_delta_if_away_win",
        "home_delta_if_draw",
        "away_delta_if_draw",
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
    parser.add_argument("--k-factor", type=float, default=K_FACTOR)
    parser.add_argument("--home-advantage", type=float, default=HOME_ADVANTAGE)
    parser.add_argument("--logistic-base", type=float, default=LOGISTIC_BASE)
    parser.add_argument("--logistic-scale", type=float, default=LOGISTIC_SCALE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    games = fetch_schedule_for_date(args.date, year=args.year)
    ratings = load_ratings(args.ranking_csv)
    probable_starters = fetch_schedule_probable_starters(args.date, year=args.year)
    for key, value in fetch_probable_starters().items():
        probable_starters.setdefault(key, value)
    rows = probability_rows(
        games,
        ratings,
        probable_starters=probable_starters,
        k_factor=args.k_factor,
        home_advantage=args.home_advantage,
        logistic_base=args.logistic_base,
        logistic_scale=args.logistic_scale,
    )
    write_csv(args.output, rows)

    print(f"Target date: {args.date}")
    print(f"Games: {len(rows)}")
    print(f"CSV: {args.output}")


if __name__ == "__main__":
    main()
