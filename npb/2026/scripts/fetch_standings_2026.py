from __future__ import annotations

import argparse
import csv
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


YEAR = 2026
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_CSV = BASE_DIR / "output" / "standings.csv"

TEAM_SHORT_NAMES = {
    "阪神タイガース": "阪神",
    "横浜DeNAベイスターズ": "DeNA",
    "読売ジャイアンツ": "巨人",
    "中日ドラゴンズ": "中日",
    "広島東洋カープ": "広島",
    "東京ヤクルトスワローズ": "ヤクルト",
    "福岡ソフトバンクホークス": "ソフトバンク",
    "北海道日本ハムファイターズ": "日本ハム",
    "千葉ロッテマリーンズ": "ロッテ",
    "東北楽天ゴールデンイーグルス": "楽天",
    "オリックス・バファローズ": "オリックス",
    "埼玉西武ライオンズ": "西武",
}

LEAGUES = [
    {
        "key": "central",
        "label": "セ・リーグ",
        "url": "https://npb.jp/bis/{year}/stats/std_c.html",
    },
    {
        "key": "pacific",
        "label": "パ・リーグ",
        "url": "https://npb.jp/bis/{year}/stats/std_p.html",
    },
]

UPDATED_RE = re.compile(r"^(\d{4})年(\d{1,2})月(\d{1,2})日\s+現在$")
PCT_RE = re.compile(r"^\.\d{3}$")


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.items: list[str] = []

    def handle_data(self, data: str) -> None:
        text = re.sub(r"\s+", " ", data).strip()
        if text and text != "\xa0":
            self.items.append(text)


def fetch_html(url: str, *, timeout: int = 20) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (npb-elo-standings/1.0)"})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def html_to_tokens(html: str) -> list[str]:
    parser = TextExtractor()
    parser.feed(html)
    return parser.items


def source_date(tokens: list[str]) -> str:
    for token in tokens:
        match = UPDATED_RE.match(token)
        if match:
            year, month, day = (int(value) for value in match.groups())
            return f"{year:04d}-{month:02d}-{day:02d}"
    return ""


def table_start(tokens: list[str]) -> int:
    header = ["チーム", "試合", "勝利", "敗北", "引分", "勝率", "差"]
    for index in range(len(tokens) - len(header)):
        if tokens[index : index + len(header)] == header:
            return index + len(header)
    raise ValueError("Could not find standings table header")


def parse_standings(tokens: list[str], *, league_key: str, league_label: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    updated = source_date(tokens)
    start = table_start(tokens)
    seen: set[str] = set()

    index = start
    while index < len(tokens) and len(rows) < 6:
        full_team = tokens[index]
        team = TEAM_SHORT_NAMES.get(full_team)
        if not team or team in seen:
            index += 1
            continue

        try:
            games = int(tokens[index + 1])
            wins = int(tokens[index + 2])
            losses = int(tokens[index + 3])
            draws = int(tokens[index + 4])
            win_pct = tokens[index + 5]
            games_behind = tokens[index + 6]
        except (IndexError, ValueError):
            index += 1
            continue

        if not PCT_RE.match(win_pct):
            index += 1
            continue

        seen.add(team)
        rows.append(
            {
                "league": league_key,
                "league_label": league_label,
                "source_date": updated,
                "rank": len(rows) + 1,
                "team": team,
                "games": games,
                "wins": wins,
                "losses": losses,
                "draws": draws,
                "win_pct": win_pct,
                "games_behind": games_behind,
            }
        )
        index += 7

    if len(rows) != 6:
        raise ValueError(f"Expected 6 standings rows for {league_label}, found {len(rows)}")
    return rows


def fetch_all_standings(*, year: int = YEAR) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for league in LEAGUES:
        url = league["url"].format(year=year)
        tokens = html_to_tokens(fetch_html(url))
        rows.extend(
            parse_standings(
                tokens,
                league_key=league["key"],
                league_label=league["label"],
            )
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "league",
        "league_label",
        "source_date",
        "rank",
        "team",
        "games",
        "wins",
        "losses",
        "draws",
        "win_pct",
        "games_behind",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch 2026 NPB standings from the official NPB site.")
    parser.add_argument("--year", type=int, default=YEAR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_CSV)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = fetch_all_standings(year=args.year)
    write_csv(args.output, rows)
    print(f"Standings rows: {len(rows)}")
    print(f"CSV: {args.output}")


if __name__ == "__main__":
    main()
