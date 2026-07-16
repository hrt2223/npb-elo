from __future__ import annotations

from .config import TEAM_COLORS, TEAM_SLUGS
from .team_pages import team_elo_history, team_elo_summary, team_games, team_recent_games, team_summary


def build_comparison_payload() -> dict[str, object]:
    teams = []
    for team in TEAM_SLUGS:
        games = team_games(team)
        history = team_elo_history(team)
        elo = team_elo_summary(history)
        recent = team_recent_games(team)
        teams.append(
            {
                "team": team,
                "color": TEAM_COLORS.get(team, "#94a3b8"),
                "elo": elo["latest"],
                "record": team_summary(games)["record"],
                "history": [
                    {"date": str(row.date), "elo": round(float(row.elo), 1)}
                    for row in history.itertuples(index=False)
                ],
                "recent": [
                    {
                        "date": str(row.date),
                        "result": str(row.result),
                        "opponent": str(row.opponent),
                        "score": str(row.score),
                        "change": round(float(row.elo_change), 1),
                    }
                    for row in recent.sort_values(["date", "game_id"], ascending=[False, False]).itertuples(index=False)
                ],
                "matchups": {
                    str(opponent): {
                        "wins": int((group["result"] == "勝").sum()),
                        "losses": int((group["result"] == "敗").sum()),
                        "draws": int((group["result"] == "分").sum()),
                    }
                    for opponent, group in games.groupby("opponent")
                }
                if not games.empty
                else {},
            }
        )
    return {"teams": teams}
