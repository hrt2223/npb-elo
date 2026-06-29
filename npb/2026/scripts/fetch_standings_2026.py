from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


YEAR = 2026
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_CSV = BASE_DIR / "game_results_jp_2026.csv"
DEFAULT_OUTPUT_CSV = BASE_DIR / "output" / "standings.csv"

COL_DATE = "日付"
COL_GAME_TYPE = "ゲームタイプ"
COL_TEAM = "球団"
COL_HOME_AWAY = "ホーム・ビジター"
COL_SCORE = "スコア"
COL_GAME_ID = "GameID"

REGULAR_SEASON = "公式戦"
HOME = "ホーム"
VISITOR = "ビジター"

LEAGUES = {
    "central": {
        "label": "セ・リーグ",
        "teams": ["阪神", "巨人", "広島", "中日", "DeNA", "ヤクルト"],
    },
    "pacific": {
        "label": "パ・リーグ",
        "teams": ["西武", "ソフトバンク", "日本ハム", "ロッテ", "オリックス", "楽天"],
    },
}


@dataclass
class TeamStanding:
    league: str
    league_label: str
    team: str
    wins: int = 0
    losses: int = 0
    draws: int = 0

    @property
    def games(self) -> int:
        return self.wins + self.losses + self.draws

    @property
    def win_pct(self) -> float:
        decisions = self.wins + self.losses
        if decisions == 0:
            return 0.0
        return self.wins / decisions


def build_initial_standings() -> dict[str, TeamStanding]:
    standings: dict[str, TeamStanding] = {}
    for league_key, league in LEAGUES.items():
        for team in league["teams"]:
            standings[team] = TeamStanding(
                league=league_key,
                league_label=str(league["label"]),
                team=team,
            )
    return standings


def read_completed_games(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    required = {COL_DATE, COL_GAME_TYPE, COL_TEAM, COL_HOME_AWAY, COL_SCORE, COL_GAME_ID}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {path}: {', '.join(sorted(missing))}")

    df = df[df[COL_GAME_TYPE] == REGULAR_SEASON].copy()
    df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce")
    df[COL_SCORE] = pd.to_numeric(df[COL_SCORE], errors="coerce")
    df = df.dropna(subset=[COL_DATE, COL_SCORE, COL_GAME_ID])
    return df


def add_result(standings: dict[str, TeamStanding], home: str, away: str, home_score: int, away_score: int) -> None:
    if home not in standings or away not in standings:
        return

    if home_score > away_score:
        standings[home].wins += 1
        standings[away].losses += 1
    elif home_score < away_score:
        standings[home].losses += 1
        standings[away].wins += 1
    else:
        standings[home].draws += 1
        standings[away].draws += 1


def calculate_standings(games_df: pd.DataFrame) -> tuple[list[TeamStanding], str]:
    standings = build_initial_standings()
    source_date = ""

    if not games_df.empty:
        source_date = games_df[COL_DATE].max().strftime("%Y-%m-%d")

    for _game_id, group in games_df.groupby(COL_GAME_ID, sort=False):
        home_rows = group[group[COL_HOME_AWAY] == HOME]
        away_rows = group[group[COL_HOME_AWAY] == VISITOR]
        if len(home_rows) != 1 or len(away_rows) != 1:
            continue

        home_row = home_rows.iloc[0]
        away_row = away_rows.iloc[0]
        add_result(
            standings,
            home=str(home_row[COL_TEAM]),
            away=str(away_row[COL_TEAM]),
            home_score=int(home_row[COL_SCORE]),
            away_score=int(away_row[COL_SCORE]),
        )

    return list(standings.values()), source_date


def format_win_pct(value: float) -> str:
    return f"{value:.3f}".lstrip("0")


def format_games_behind(first: TeamStanding, team: TeamStanding) -> str:
    if team is first:
        return "--"

    games_behind = ((first.wins - team.wins) + (team.losses - first.losses)) / 2
    if games_behind == 0:
        return "0.0"
    return f"{games_behind:.1f}"


def rows_for_csv(standings: list[TeamStanding], source_date: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for league_key in LEAGUES:
        league_rows = [standing for standing in standings if standing.league == league_key]
        team_order = {team: index for index, team in enumerate(LEAGUES[league_key]["teams"])}
        league_rows.sort(
            key=lambda item: (
                -item.win_pct,
                -item.wins,
                item.losses,
                team_order.get(item.team, len(team_order)),
            )
        )
        first = league_rows[0]

        for rank, standing in enumerate(league_rows, start=1):
            rows.append(
                {
                    "league": standing.league,
                    "league_label": standing.league_label,
                    "source_date": source_date,
                    "rank": rank,
                    "team": standing.team,
                    "games": standing.games,
                    "wins": standing.wins,
                    "losses": standing.losses,
                    "draws": standing.draws,
                    "win_pct": format_win_pct(standing.win_pct),
                    "games_behind": format_games_behind(first, standing),
                }
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
    parser = argparse.ArgumentParser(description="Build 2026 NPB standings from completed game results.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_CSV)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--year", type=int, default=YEAR, help="Kept for compatibility with the old fetch command.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    games_df = read_completed_games(args.input)
    standings, source_date = calculate_standings(games_df)
    rows = rows_for_csv(standings, source_date)
    write_csv(args.output, rows)
    print(f"Standings rows: {len(rows)}")
    print(f"Source date: {source_date}")
    print(f"CSV: {args.output}")


if __name__ == "__main__":
    main()
