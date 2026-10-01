from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE = BASE_DIR / "research" / "npb_2026_player_stats.sqlite"
DEFAULT_OUTPUT_DIR = BASE_DIR / "research" / "team_exports"


def write_csv(path: Path, rows: list[sqlite3.Row]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(dict(row) for row in rows)


def export_team_data(database: Path, output_dir: Path) -> list[str]:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    teams = [row[0] for row in connection.execute("SELECT DISTINCT team FROM batting_game_stats ORDER BY team")]
    for team in teams:
        batting = connection.execute(
            """
            SELECT g.date, g.game_id, b.team, b.player_name, b.batting_order,
                   p.games_appeared_before, p.ab_before, p.hits_before,
                   p.doubles_before, p.triples_before, p.home_runs_before,
                   p.walks_before, p.hit_by_pitch_before, p.sacrifice_flies_before,
                   p.obp, p.slg, p.ops
            FROM batting_game_stats b
            JOIN games g ON g.game_id = b.game_id
            JOIN batting_pregame_stats p ON p.game_id = b.game_id AND p.player_id = b.player_id
            WHERE b.team = ?
            ORDER BY g.date, g.game_id, b.batting_order, b.player_name
            """,
            (team,),
        ).fetchall()
        pitching = connection.execute(
            """
            SELECT g.date, g.game_id, p.team, p.player_name, p.is_starter,
                   s.games_appeared_before, s.starts_before, s.outs_before,
                   s.earned_runs_before, s.hits_allowed_before, s.walks_before,
                   s.hit_by_pitch_before, s.strikeouts_before, s.era, s.whip
            FROM pitching_game_stats p
            JOIN games g ON g.game_id = p.game_id
            JOIN pitching_pregame_stats s ON s.game_id = p.game_id AND s.player_id = p.player_id
            WHERE p.team = ?
            ORDER BY g.date, g.game_id, p.is_starter DESC, p.player_name
            """,
            (team,),
        ).fetchall()
        write_csv(output_dir / f"{team}_batting_pregame.csv", batting)
        write_csv(output_dir / f"{team}_pitching_pregame.csv", pitching)
    return teams


def main() -> None:
    parser = argparse.ArgumentParser(description="Export research player snapshots into per-team CSV files.")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    teams = export_team_data(args.database, args.output_dir)
    print(f"Teams exported: {len(teams)}")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
