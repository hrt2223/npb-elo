from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

from elo import (
    HOME_ADVANTAGE,
    INITIAL_RATING,
    K_FACTOR,
    calculate_elo,
    load_games,
    write_outputs,
)


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = BASE_DIR / "game_results_jp_2026.csv"
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"
DEFAULT_LOG_DIR = BASE_DIR / "logs"
INTERLEAGUE_START = pd.Timestamp("2026-05-26")
INTERLEAGUE_END = pd.Timestamp("2026-06-18")

LEAGUES = {
    "central": {"阪神", "DeNA", "巨人", "中日", "広島", "ヤクルト"},
    "pacific": {"ソフトバンク", "日本ハム", "オリックス", "楽天", "西武", "ロッテ"},
}

LEAGUE_LABELS = {
    "overall": "All NPB",
    "central": "Central League",
    "pacific": "Pacific League",
    "interleague": "Interleague",
}

EMPTY_OUTPUT_COLUMNS = {
    "games.csv": [
        "date",
        "game_id",
        "home",
        "away",
        "home_score",
        "away_score",
        "stadium",
        "start_time",
    ],
    "elo_final_ranking.csv": ["rank", "team", "final_elo"],
    "elo_by_game.csv": [
        "date",
        "game_id",
        "home",
        "away",
        "home_score",
        "away_score",
        "stadium",
        "start_time",
        "home_elo_before",
        "away_elo_before",
        "home_expected_win_rate",
        "home_elo_change",
        "home_elo_after",
        "away_elo_after",
    ],
    "elo_history.csv": ["date", "team", "elo"],
}


def format_ranking(ranking_df) -> str:
    return ranking_df.to_string(index=False, formatters={"final_elo": "{:.1f}".format})


def write_latest_summary(
    output_dir: Path,
    *,
    label: str,
    csv_path: Path,
    game_count: int,
    start_date,
    end_date,
    ranking_text: str,
) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"2026 NPB Elo latest ranking - {label}",
        f"Updated at: {now}",
        f"CSV: {csv_path}",
        f"Games: {game_count}",
        f"Period: {start_date.date()} - {end_date.date()}",
        "",
        ranking_text,
        "",
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "elo_latest.txt").write_text("\n".join(lines), encoding="utf-8")


def write_no_games_summary(output_dir: Path, *, label: str, csv_path: Path) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"2026 NPB Elo latest ranking - {label}",
        f"Updated at: {now}",
        f"CSV: {csv_path}",
        "Games: 0",
        "",
        "No games found.",
        "",
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "elo_latest.txt").write_text("\n".join(lines), encoding="utf-8")


def write_empty_outputs(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, columns in EMPTY_OUTPUT_COLUMNS.items():
        pd.DataFrame(columns=columns).to_csv(output_dir / filename, index=False, encoding="utf-8-sig")


def append_log(
    log_dir: Path,
    *,
    label: str,
    csv_path: Path,
    game_count: int,
    start_date,
    end_date,
    ranking_text: str,
) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "=" * 72,
        f"Target: {label}",
        f"Updated at: {now}",
        f"CSV: {csv_path}",
        f"Games: {game_count}",
        f"Period: {start_date.date()} - {end_date.date()}",
        ranking_text,
        "",
    ]
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / "update.log").open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))


def append_no_games_log(log_dir: Path, *, label: str, csv_path: Path) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "=" * 72,
        f"Target: {label}",
        f"Updated at: {now}",
        f"CSV: {csv_path}",
        "Games: 0",
        "No games found.",
        "",
    ]
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / "update.log").open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))


def update_outputs_from_frames(
    games_df: pd.DataFrame,
    ranking_df: pd.DataFrame,
    by_game_df: pd.DataFrame,
    history_df: pd.DataFrame,
    *,
    label: str,
    csv_path: Path,
    output_dir: Path,
    log_dir: Path,
) -> None:
    if games_df.empty:
        write_empty_outputs(output_dir)
        write_no_games_summary(output_dir, label=label, csv_path=csv_path)
        append_no_games_log(log_dir, label=label, csv_path=csv_path)
        return

    write_outputs(output_dir, games_df, ranking_df, by_game_df, history_df)

    ranking_text = format_ranking(ranking_df)
    write_latest_summary(
        output_dir,
        label=label,
        csv_path=csv_path,
        game_count=len(games_df),
        start_date=games_df["date"].min(),
        end_date=games_df["date"].max(),
        ranking_text=ranking_text,
    )
    append_log(
        log_dir,
        label=label,
        csv_path=csv_path,
        game_count=len(games_df),
        start_date=games_df["date"].min(),
        end_date=games_df["date"].max(),
        ranking_text=ranking_text,
    )


def league_frames(
    games_df: pd.DataFrame,
    ranking_df: pd.DataFrame,
    by_game_df: pd.DataFrame,
    history_df: pd.DataFrame,
    teams: set[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    games_mask = games_df["home"].isin(teams) | games_df["away"].isin(teams)
    by_game_mask = by_game_df["home"].isin(teams) | by_game_df["away"].isin(teams)

    league_games_df = games_df[games_mask].reset_index(drop=True)
    league_by_game_df = by_game_df[by_game_mask].reset_index(drop=True)
    league_history_df = history_df[history_df["team"].isin(teams)].reset_index(drop=True)
    league_ranking_df = (
        ranking_df[ranking_df["team"].isin(teams)]
        .drop(columns=["rank"], errors="ignore")
        .sort_values("final_elo", ascending=False)
        .reset_index(drop=True)
    )
    league_ranking_df.insert(0, "rank", league_ranking_df.index + 1)

    return league_games_df, league_ranking_df, league_by_game_df, league_history_df


def interleague_frames(
    games_df: pd.DataFrame,
    by_game_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    games_mask = games_df["date"].between(INTERLEAGUE_START, INTERLEAGUE_END)
    by_game_mask = by_game_df["date"].between(INTERLEAGUE_START, INTERLEAGUE_END)

    interleague_games_df = games_df[games_mask].reset_index(drop=True)
    interleague_by_game_df = by_game_df[by_game_mask].reset_index(drop=True)

    if interleague_by_game_df.empty:
        ranking_df = pd.DataFrame(columns=["rank", "team", "final_elo"])
        history_df = pd.DataFrame(columns=["date", "team", "elo"])
        return interleague_games_df, ranking_df, interleague_by_game_df, history_df

    home_after = interleague_by_game_df[["date", "home", "home_elo_after"]].rename(
        columns={"home": "team", "home_elo_after": "elo"}
    )
    away_after = interleague_by_game_df[["date", "away", "away_elo_after"]].rename(
        columns={"away": "team", "away_elo_after": "elo"}
    )
    history_df = (
        pd.concat([home_after, away_after], ignore_index=True)
        .sort_values(["date", "team"])
        .reset_index(drop=True)
    )

    latest = (
        history_df.sort_values(["date"])
        .groupby("team", as_index=False)
        .tail(1)[["team", "elo"]]
        .rename(columns={"elo": "final_elo"})
        .sort_values("final_elo", ascending=False)
        .reset_index(drop=True)
    )
    latest.insert(0, "rank", latest.index + 1)

    return interleague_games_df, latest, interleague_by_game_df, history_df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update 2026 NPB Elo outputs from a local CSV.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to 2026 game results CSV")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument("--initial-rating", type=float, default=INITIAL_RATING)
    parser.add_argument("--k-factor", type=float, default=K_FACTOR)
    parser.add_argument("--home-advantage", type=float, default=HOME_ADVANTAGE)
    parser.add_argument("--include-non-regular", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    csv_path = args.csv.resolve()

    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV not found: {csv_path}\n"
            "Place the current 2026 results CSV there, or pass --csv path\\to\\file.csv"
        )

    try:
        games_df = load_games(csv_path, regular_season_only=not args.include_non_regular)
    except ValueError as exc:
        if "No games were found" not in str(exc):
            raise

        write_empty_outputs(args.output_dir)
        write_no_games_summary(args.output_dir, label=LEAGUE_LABELS["overall"], csv_path=csv_path)
        append_no_games_log(args.log_dir, label=LEAGUE_LABELS["overall"], csv_path=csv_path)
        for league_name in LEAGUES:
            write_empty_outputs(args.output_dir / league_name)
            write_no_games_summary(
                args.output_dir / league_name,
                label=LEAGUE_LABELS[league_name],
                csv_path=csv_path,
            )
            append_no_games_log(
                args.log_dir,
                label=LEAGUE_LABELS[league_name],
                csv_path=csv_path,
            )
        write_empty_outputs(args.output_dir / "interleague")
        write_no_games_summary(
            args.output_dir / "interleague",
            label=LEAGUE_LABELS["interleague"],
            csv_path=csv_path,
        )
        append_no_games_log(
            args.log_dir,
            label=LEAGUE_LABELS["interleague"],
            csv_path=csv_path,
        )

        print("Daily Elo update completed")
        print("Games: 0")
        print("No games found.")
        print(f"Output: {args.output_dir}")
        print(f"Log: {args.log_dir / 'update.log'}")
        return

    ranking_df, by_game_df, history_df = calculate_elo(
        games_df,
        initial_rating=args.initial_rating,
        k_factor=args.k_factor,
        home_advantage=args.home_advantage,
    )

    update_outputs_from_frames(
        games_df,
        ranking_df,
        by_game_df,
        history_df,
        label=LEAGUE_LABELS["overall"],
        csv_path=csv_path,
        output_dir=args.output_dir,
        log_dir=args.log_dir,
    )

    league_game_counts = {}
    for league_name, teams in LEAGUES.items():
        league_games_df, league_ranking_df, league_by_game_df, league_history_df = league_frames(
            games_df,
            ranking_df,
            by_game_df,
            history_df,
            teams,
        )
        league_game_counts[league_name] = len(league_games_df)
        update_outputs_from_frames(
            league_games_df,
            league_ranking_df,
            league_by_game_df,
            league_history_df,
            label=LEAGUE_LABELS[league_name],
            csv_path=csv_path,
            output_dir=args.output_dir / league_name,
            log_dir=args.log_dir,
        )

    interleague_games_df, interleague_ranking_df, interleague_by_game_df, interleague_history_df = interleague_frames(
        games_df,
        by_game_df,
    )
    update_outputs_from_frames(
        interleague_games_df,
        interleague_ranking_df,
        interleague_by_game_df,
        interleague_history_df,
        label=LEAGUE_LABELS["interleague"],
        csv_path=csv_path,
        output_dir=args.output_dir / "interleague",
        log_dir=args.log_dir,
    )

    ranking_text = format_ranking(ranking_df)

    print("Daily Elo update completed")
    print(f"Games: {len(games_df)}")
    print(f"Central League games: {league_game_counts['central']}")
    print(f"Pacific League games: {league_game_counts['pacific']}")
    print(f"Interleague games: {len(interleague_games_df)}")
    print(f"Output: {args.output_dir}")
    print(f"Log: {args.log_dir / 'update.log'}")
    print()
    print(ranking_text)


if __name__ == "__main__":
    main()
