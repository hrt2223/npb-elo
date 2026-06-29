from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from elo_settings import (
    HOME_ADVANTAGE,
    INITIAL_RATING,
    K_FACTOR,
    LOGISTIC_BASE,
    LOGISTIC_SCALE,
)


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


@dataclass(frozen=True)
class Game:
    date: pd.Timestamp#日付
    game_id: str
    home: str
    away: str
    home_score: int#ホームチームのスコア
    away_score: int#ビジターチームのスコア


#eloレーティングの予想勝率を計算する式
def expected_score(
    rating_a: float,
    rating_b: float,
    *,
    logistic_base: float = LOGISTIC_BASE,
    logistic_scale: float = LOGISTIC_SCALE,
) -> float:
    """Return player/team A's expected score against B."""
    if logistic_base <= 1.0:
        raise ValueError("logistic_base must be greater than 1")
    if logistic_scale <= 0.0:
        raise ValueError("logistic_scale must be greater than 0")
    return 1.0 / (1.0 + logistic_base ** ((rating_b - rating_a) / logistic_scale))


def actual_score(score_a: int, score_b: int) -> float:
    if score_a > score_b:#勝ち
        return 1.0
    if score_a < score_b:#負け
        return 0.0
    return 0.5#引き分け


def update_ratings(
    home_rating: float,#ホームチームのレーティング
    away_rating: float,#ビジターチームのレーティング
    home_score: int,#ホームチームのスコア
    away_score: int,#ビジターチームのスコア
    *,
    k_factor: float = K_FACTOR,
    home_advantage: float = HOME_ADVANTAGE,
    logistic_base: float = LOGISTIC_BASE,
    logistic_scale: float = LOGISTIC_SCALE,
) -> tuple[float, float, float, float]:
    expected_home = expected_score(
        home_rating + home_advantage,
        away_rating,
        logistic_base=logistic_base,
        logistic_scale=logistic_scale,
    )
    actual_home = actual_score(home_score, away_score)
    change = k_factor * (actual_home - expected_home)
    return (
        home_rating + change,
        away_rating - change,
        expected_home,
        change,
    )

#チーム名を短縮する関数
def short_team_name(name: str) -> str:
    return TEAM_SHORT_NAMES.get(name, name)

#CSVを読み込んで、日付列を日付型に変換している
def load_games(csv_path: Path, *, regular_season_only: bool = True) -> pd.DataFrame:
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df["日付"] = pd.to_datetime(df["日付"])

    if regular_season_only and "ゲームタイプ" in df.columns:
        df = df[df["ゲームタイプ"] == "公式戦"].copy()
#game_idごとにグループ化して、ホームとビジターチームの行を分けている
    games: list[Game] = []
    for game_id, group in df.groupby("GameID", sort=False):
        home_rows = group[group["ホーム・ビジター"] == "ホーム"]
        away_rows = group[group["ホーム・ビジター"] == "ビジター"]

        if len(home_rows) != 1 or len(away_rows) != 1:
            continue

        home = home_rows.iloc[0]
        away = away_rows.iloc[0]

#gameに試合の情報をつめてる。
        games.append(
            Game(
                date=home["日付"],
                game_id=str(game_id),
                home=short_team_name(str(home["球団"])),
                away=short_team_name(str(away["球団"])),
                home_score=int(home["スコア"]),
                away_score=int(away["スコア"]),
            )
        )

    if not games:
        raise ValueError(f"No games were found in {csv_path}")

    game_df = pd.DataFrame([game.__dict__ for game in games])
    return game_df.sort_values(["date", "game_id"]).reset_index(drop=True)


def calculate_elo(
    game_df: pd.DataFrame,
    *,
    initial_rating: float = INITIAL_RATING,
    k_factor: float = K_FACTOR,
    home_advantage: float = HOME_ADVANTAGE,
    logistic_base: float = LOGISTIC_BASE,
    logistic_scale: float = LOGISTIC_SCALE,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    teams = sorted(set(game_df["home"]) | set(game_df["away"]))
    ratings = {team: initial_rating for team in teams}

    game_records = []
    history_records = [
        {
            "date": game_df["date"].min() - pd.Timedelta(days=1),
            "team": team,
            "elo": initial_rating,
        }
        for team in teams
    ]

    for row in game_df.itertuples(index=False):
        old_home = ratings[row.home]
        old_away = ratings[row.away]
        new_home, new_away, expected_home, change = update_ratings(
            old_home,
            old_away,
            row.home_score,
            row.away_score,
            k_factor=k_factor,
            home_advantage=home_advantage,
            logistic_base=logistic_base,
            logistic_scale=logistic_scale,
        )

        ratings[row.home] = new_home
        ratings[row.away] = new_away

        game_records.append(
            {
                "date": row.date,
                "game_id": row.game_id,
                "home": row.home,
                "away": row.away,
                "home_score": row.home_score,
                "away_score": row.away_score,
                "home_elo_before": old_home,
                "away_elo_before": old_away,
                "home_expected_win_rate": expected_home,
                "home_elo_change": change,
                "home_elo_after": new_home,
                "away_elo_after": new_away,
            }
        )

        for team in teams:
            history_records.append({"date": row.date, "team": team, "elo": ratings[team]})

    ranking_df = (
        pd.DataFrame({"team": ratings.keys(), "final_elo": ratings.values()})
        .sort_values("final_elo", ascending=False)
        .reset_index(drop=True)
    )
    ranking_df.insert(0, "rank", ranking_df.index + 1)

    return ranking_df, pd.DataFrame(game_records), pd.DataFrame(history_records)


def write_outputs(
    output_dir: Path,
    games_df: pd.DataFrame,
    ranking_df: pd.DataFrame,
    by_game_df: pd.DataFrame,
    history_df: pd.DataFrame,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    games_df.to_csv(output_dir / "games.csv", index=False, encoding="utf-8-sig")
    ranking_df.to_csv(output_dir / "elo_final_ranking.csv", index=False, encoding="utf-8-sig")
    by_game_df.to_csv(output_dir / "elo_by_game.csv", index=False, encoding="utf-8-sig")
    history_df.to_csv(output_dir / "elo_history.csv", index=False, encoding="utf-8-sig")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calculate Elo ratings from NPB game results CSV.")
    parser.add_argument("csv", type=Path, help="Path to game results CSV")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--initial-rating", type=float, default=INITIAL_RATING)
    parser.add_argument("--k-factor", type=float, default=K_FACTOR)
    parser.add_argument("--home-advantage", type=float, default=HOME_ADVANTAGE)
    parser.add_argument("--logistic-base", type=float, default=LOGISTIC_BASE)
    parser.add_argument("--logistic-scale", type=float, default=LOGISTIC_SCALE)
    parser.add_argument("--include-non-regular", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    games_df = load_games(args.csv, regular_season_only=not args.include_non_regular)
    ranking_df, by_game_df, history_df = calculate_elo(
        games_df,
        initial_rating=args.initial_rating,
        k_factor=args.k_factor,
        home_advantage=args.home_advantage,
        logistic_base=args.logistic_base,
        logistic_scale=args.logistic_scale,
    )

    write_outputs(args.output_dir, games_df, ranking_df, by_game_df, history_df)

    print("Final Elo ranking")
    print(ranking_df.to_string(index=False, formatters={"final_elo": "{:.1f}".format}))
    print(f"\nSaved CSV files to: {args.output_dir}")


if __name__ == "__main__":
    main()
