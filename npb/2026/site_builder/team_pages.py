from __future__ import annotations

import html
from pathlib import Path

import pandas as pd

from .config import LEAGUE_LABELS, LEAGUE_TEAMS, OUTPUT_DIR, SITE_DIR, TEAM_COLORS, TEAM_SLUGS
from .tables import read_csv


def team_page_path(league_key: str, team: str) -> Path:
    return SITE_DIR / league_key / f"{TEAM_SLUGS[team]}.html"


def team_page_href(league_key: str, team: str) -> str:
    return f"{league_key}/{TEAM_SLUGS[team]}.html"


def build_team_links_html(league_key: str) -> str:
    teams = LEAGUE_TEAMS.get(league_key, [])
    if not teams:
        return ""

    links = []
    for team in teams:
        color = TEAM_COLORS.get(team, "#38bdf8")
        links.append(
            f'<a class="team-link" href="{html.escape(team_page_href(league_key, team))}">'
            f'<span class="team-dot" style="background:{html.escape(color)}"></span>'
            f"{html.escape(team)}</a>"
        )
    return '<div class="team-links">' + "".join(links) + "</div>"


def result_label(score: int, opponent_score: int) -> str:
    if score > opponent_score:
        return "勝"
    if score < opponent_score:
        return "敗"
    return "分"


def result_class(result: str) -> str:
    if result == "勝":
        return "win"
    if result == "敗":
        return "loss"
    return "draw"


def team_games(team: str) -> pd.DataFrame:
    by_game_df = read_csv(OUTPUT_DIR / "elo_by_game.csv")
    if by_game_df.empty:
        return pd.DataFrame()

    records = []
    for _, row in by_game_df.iterrows():
        if row["home"] == team:
            score = int(row["home_score"])
            opponent_score = int(row["away_score"])
            before = float(row["home_elo_before"])
            after = float(row["home_elo_after"])
            opponent = row["away"]
            venue = "ホーム"
        elif row["away"] == team:
            score = int(row["away_score"])
            opponent_score = int(row["home_score"])
            before = float(row["away_elo_before"])
            after = float(row["away_elo_after"])
            opponent = row["home"]
            venue = "ビジター"
        else:
            continue

        change = after - before
        result = result_label(score, opponent_score)
        records.append(
            {
                "date": row["date"],
                "game_id": row["game_id"],
                "result": result,
                "opponent": opponent,
                "venue": venue,
                "score": f"{score}-{opponent_score}",
                "elo_before": before,
                "elo_after": after,
                "elo_change": change,
                "elo_change_rate": (change / before) * 100 if before else 0.0,
            }
        )

    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records).sort_values(["date", "game_id"]).reset_index(drop=True)


def team_recent_games(team: str, *, limit: int = 10) -> pd.DataFrame:
    games_df = team_games(team)
    if games_df.empty:
        return games_df
    return games_df.tail(limit).reset_index(drop=True)


def team_elo_history(team: str) -> pd.DataFrame:
    history_df = read_csv(OUTPUT_DIR / "elo_history.csv")
    if history_df.empty:
        return pd.DataFrame()
    return history_df[history_df["team"] == team].sort_values("date").reset_index(drop=True)


def team_elo_summary(history_df: pd.DataFrame) -> dict[str, str]:
    if history_df.empty:
        return {"latest": "-", "peak": "-", "low": "-", "change": "-"}

    first = float(history_df.iloc[0]["elo"])
    latest = float(history_df.iloc[-1]["elo"])
    peak_row = history_df.loc[history_df["elo"].idxmax()]
    low_row = history_df.loc[history_df["elo"].idxmin()]
    return {
        "latest": f"{latest:.1f}",
        "peak": f"{float(peak_row['elo']):.1f} ({html.escape(str(peak_row['date']))})",
        "low": f"{float(low_row['elo']):.1f} ({html.escape(str(low_row['date']))})",
        "change": f"{latest - first:+.1f}",
    }


def team_summary(games_df: pd.DataFrame) -> dict[str, str]:
    if games_df.empty:
        return {"record": "0勝 0敗 0分", "games": "0"}

    wins = int((games_df["result"] == "勝").sum())
    losses = int((games_df["result"] == "敗").sum())
    draws = int((games_df["result"] == "分").sum())
    return {"record": f"{wins}勝 {losses}敗 {draws}分", "games": str(len(games_df))}


def team_streaks(games_df: pd.DataFrame) -> dict[str, str]:
    if games_df.empty:
        return {"max_win": "0", "max_loss": "0", "current": "-"}

    max_win = 0
    max_loss = 0
    current_kind = ""
    current_count = 0

    for result in games_df["result"]:
        kind = result_class(str(result))
        if kind == "win":
            current_count = current_count + 1 if current_kind == "win" else 1
            current_kind = "win"
            max_win = max(max_win, current_count)
        elif kind == "loss":
            current_count = current_count + 1 if current_kind == "loss" else 1
            current_kind = "loss"
            max_loss = max(max_loss, current_count)
        else:
            current_kind = ""
            current_count = 0

    if current_kind == "win":
        current = f"{current_count}連勝中"
    elif current_kind == "loss":
        current = f"{current_count}連敗中"
    else:
        current = "連勝/連敗なし"

    return {"max_win": str(max_win), "max_loss": str(max_loss), "current": current}


def team_elo_sparkline_html(history_df: pd.DataFrame) -> str:
    if history_df.empty:
        return '<div class="empty">Elo推移データがありません</div>'

    values = [float(value) for value in history_df["elo"]]
    if len(values) == 1:
        values.append(values[0])
    min_value = min(values)
    max_value = max(values)
    spread = max(max_value - min_value, 1.0)
    width = 880
    height = 220
    pad_x = 30
    pad_y = 24
    usable_w = width - pad_x * 2
    usable_h = height - pad_y * 2
    points = []

    for index, value in enumerate(values):
        x = pad_x + usable_w * (index / max(len(values) - 1, 1))
        y = pad_y + usable_h * (1 - ((value - min_value) / spread))
        points.append(f"{x:.1f},{y:.1f}")

    latest_x, latest_y = points[-1].split(",")
    return f"""
    <div class="sparkline-wrap">
      <svg class="sparkline" viewBox="0 0 {width} {height}" role="img" aria-label="Elo推移">
        <line class="axis" x1="{pad_x}" y1="{pad_y}" x2="{pad_x}" y2="{height - pad_y}" />
        <line class="axis" x1="{pad_x}" y1="{height - pad_y}" x2="{width - pad_x}" y2="{height - pad_y}" />
        <polyline class="trend" points="{' '.join(points)}" />
        <circle class="latest-point" cx="{latest_x}" cy="{latest_y}" r="5" />
        <text x="{width - pad_x}" y="{pad_y + 6}" text-anchor="end">latest {values[-1]:.1f}</text>
        <text x="{pad_x + 4}" y="{pad_y + 6}">max {max_value:.1f}</text>
        <text x="{pad_x + 4}" y="{height - 7}">min {min_value:.1f}</text>
      </svg>
    </div>
    """


def head_to_head_df(team: str) -> pd.DataFrame:
    games_df = team_games(team)
    if games_df.empty:
        return pd.DataFrame()

    rows = []
    for opponent, group in games_df.groupby("opponent", sort=False):
        classes = group["result"].map(result_class)
        wins = int((classes == "win").sum())
        losses = int((classes == "loss").sum())
        draws = int((classes == "draw").sum())
        runs_for = 0
        runs_against = 0
        for score_text in group["score"]:
            score, opponent_score = str(score_text).split("-", maxsplit=1)
            runs_for += int(score)
            runs_against += int(opponent_score)
        games = wins + losses + draws
        win_pct = wins / (wins + losses) if (wins + losses) else 0.0
        rows.append(
            {
                "opponent": opponent,
                "games": games,
                "record": f"{wins}勝 {losses}敗 {draws}分",
                "win_pct": win_pct,
                "runs": f"{runs_for}-{runs_against}",
                "diff": runs_for - runs_against,
            }
        )

    return pd.DataFrame(rows).sort_values(["win_pct", "diff", "games"], ascending=[False, False, False])


def head_to_head_html(team: str) -> str:
    df = head_to_head_df(team)
    if df.empty:
        return '<div class="empty">対戦相性データがありません</div>'

    rows = []
    for _, row in df.iterrows():
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(row['opponent']))}</td>"
            f"<td>{int(row['games'])}</td>"
            f"<td>{html.escape(str(row['record']))}</td>"
            f"<td>{float(row['win_pct']):.3f}</td>"
            f"<td>{html.escape(str(row['runs']))}</td>"
            f"<td>{int(row['diff']):+d}</td>"
            "</tr>"
        )

    header = "<tr><th>相手</th><th>試合</th><th>成績</th><th>勝率</th><th>得失点</th><th>差</th></tr>"
    return f"<table><thead>{header}</thead><tbody>{''.join(rows)}</tbody></table>"


def team_recent_table_html(recent_df: pd.DataFrame) -> str:
    if recent_df.empty:
        return '<div class="empty">データがありません</div>'

    rows = []
    display_df = recent_df.sort_values(["date", "game_id"], ascending=[False, False])
    for _, row in display_df.iterrows():
        result = str(row["result"])
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(row['date']))}</td>"
            f'<td><span class="result {result_class(result)}">{html.escape(result)}</span></td>'
            f"<td>{html.escape(str(row['opponent']))}</td>"
            f"<td>{html.escape(str(row['venue']))}</td>"
            f"<td>{html.escape(str(row['score']))}</td>"
            f"<td>{float(row['elo_before']):.1f}</td>"
            f"<td>{float(row['elo_after']):.1f}</td>"
            f"<td>{float(row['elo_change']):+.1f}</td>"
            f"<td>{float(row['elo_change_rate']):+.2f}%</td>"
            "</tr>"
        )

    header = (
        "<tr><th>日付</th><th>結果</th><th>相手</th><th>球場区分</th><th>スコア</th>"
        "<th>試合前Elo</th><th>試合後Elo</th><th>変化</th><th>変化率</th></tr>"
    )
    return f"<table><thead>{header}</thead><tbody>{''.join(rows)}</tbody></table>"


def build_team_page_html(*, league_key: str, league_label: str, team: str) -> str:
    games_df = team_games(team)
    recent_df = games_df.tail(10).reset_index(drop=True) if not games_df.empty else pd.DataFrame()
    history_df = team_elo_history(team)
    record_summary = team_summary(games_df)
    elo_summary = team_elo_summary(history_df)
    streaks = team_streaks(games_df)
    table_html = team_recent_table_html(recent_df)
    trend_html = team_elo_sparkline_html(history_df)
    matchup_html = head_to_head_html(team)
    latest_date = str(games_df["date"].max()) if not games_df.empty else "-"
    color = TEAM_COLORS.get(team, "#38bdf8")

    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(team)} - 2026 NPB Elo</title>
  <style>
    :root {{
      --bg: #07090d;
      --surface: #10141d;
      --surface-2: #151b26;
      --ink: #edf2f7;
      --muted: #9aa4b2;
      --line: #252d3a;
      --accent: #38bdf8;
      --team: {html.escape(color)};
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: "Yu Gothic", "Meiryo", system-ui, sans-serif;
      background:
        radial-gradient(circle at 50% -18%, color-mix(in srgb, var(--team) 24%, transparent), transparent 35%),
        linear-gradient(180deg, #0b111a 0%, var(--bg) 42%, #050608 100%);
      color: var(--ink);
    }}
    main {{
      max-width: 1160px;
      margin: 0 auto;
      padding: 28px 22px 40px;
    }}
    a {{
      color: #7dd3fc;
      text-decoration: none;
      font-weight: 700;
    }}
    a:hover {{ text-decoration: underline; }}
    .back {{
      display: inline-flex;
      margin-bottom: 18px;
      color: var(--muted);
      font-size: 14px;
    }}
    .hero {{
      border: 1px solid var(--line);
      border-radius: 10px;
      background: linear-gradient(180deg, rgba(21, 27, 38, 0.96), rgba(10, 14, 21, 0.96));
      padding: 22px;
      box-shadow: 0 18px 55px rgba(0, 0, 0, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.04);
      margin-bottom: 16px;
    }}
    .league {{
      color: var(--muted);
      font-size: 14px;
      margin-bottom: 6px;
    }}
    h1 {{
      margin: 0;
      font-size: 34px;
      line-height: 1.15;
      letter-spacing: 0;
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .dot {{
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: var(--team);
      box-shadow: 0 0 26px var(--team);
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }}
    .metric {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(16, 20, 29, 0.94);
      padding: 14px 16px;
      min-height: 78px;
    }}
    .metric-label {{
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }}
    .metric-value {{
      font-size: 20px;
      font-weight: 800;
      color: #f8fafc;
      overflow-wrap: anywhere;
    }}
    .grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(360px, 0.9fr);
      gap: 16px;
      margin-bottom: 16px;
      align-items: start;
    }}
    .stack {{
      display: grid;
      gap: 16px;
    }}
    .panel {{
      border: 1px solid var(--line);
      border-radius: 10px;
      background: rgba(16, 20, 29, 0.94);
      overflow: hidden;
      box-shadow: 0 18px 55px rgba(0, 0, 0, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.035);
    }}
    .panel-header {{
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      background: rgba(21, 27, 38, 0.72);
      font-weight: 800;
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
    }}
    .panel-header span {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
    }}
    .sparkline-wrap {{
      padding: 14px;
    }}
    .sparkline {{
      width: 100%;
      aspect-ratio: 4 / 1;
      display: block;
    }}
    .sparkline .axis {{
      stroke: #334155;
      stroke-width: 1;
    }}
    .sparkline .trend {{
      fill: none;
      stroke: var(--team);
      stroke-width: 4;
      stroke-linecap: round;
      stroke-linejoin: round;
    }}
    .sparkline .latest-point {{
      fill: #f8fafc;
      stroke: var(--team);
      stroke-width: 3;
    }}
    .sparkline text {{
      fill: #cbd5e1;
      font-size: 14px;
      font-weight: 800;
    }}
    .table-wrap {{ overflow-x: auto; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      white-space: nowrap;
      color: #dbe3ee;
    }}
    th, td {{
      padding: 10px 11px;
      border-bottom: 1px solid #202733;
      text-align: right;
    }}
    th {{
      background: #151b26;
      color: #cbd5e1;
      font-weight: 800;
    }}
    th:first-child, td:first-child,
    th:nth-child(3), td:nth-child(3),
    th:nth-child(4), td:nth-child(4) {{
      text-align: left;
    }}
    tbody tr:hover {{
      background: rgba(56, 189, 248, 0.06);
    }}
    .result {{
      display: inline-grid;
      place-items: center;
      min-width: 24px;
      height: 24px;
      border-radius: 999px;
      padding: 0 6px;
      font-weight: 900;
    }}
    .result.win {{ color: #062e18; background: #4ade80; }}
    .result.loss {{ color: #3f0b0b; background: #f87171; }}
    .result.draw {{ color: #1f2937; background: #cbd5e1; }}
    .empty {{ padding: 24px; color: var(--muted); }}
    @media (max-width: 860px) {{
      .summary {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .grid {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 28px; }}
    }}
    @media (max-width: 520px) {{
      main {{ padding: 20px 14px 32px; }}
      .summary {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <a class="back" href="../index.html">← ダッシュボードへ戻る</a>
    <section class="hero">
      <div class="league">{html.escape(league_label)}</div>
      <h1><span class="dot"></span>{html.escape(team)}</h1>
    </section>

    <section class="summary">
      <div class="metric">
        <div class="metric-label">試合数</div>
        <div class="metric-value">{html.escape(record_summary["games"])}</div>
      </div>
      <div class="metric">
        <div class="metric-label">成績</div>
        <div class="metric-value">{html.escape(record_summary["record"])}</div>
      </div>
      <div class="metric">
        <div class="metric-label">現在Elo</div>
        <div class="metric-value">{html.escape(elo_summary["latest"])}</div>
      </div>
      <div class="metric">
        <div class="metric-label">開幕からのElo変化</div>
        <div class="metric-value">{html.escape(elo_summary["change"])}</div>
      </div>
      <div class="metric">
        <div class="metric-label">最高Elo</div>
        <div class="metric-value">{html.escape(elo_summary["peak"])}</div>
      </div>
      <div class="metric">
        <div class="metric-label">最低Elo</div>
        <div class="metric-value">{html.escape(elo_summary["low"])}</div>
      </div>
      <div class="metric">
        <div class="metric-label">最大連勝 / 最大連敗</div>
        <div class="metric-value">{html.escape(streaks["max_win"])} / {html.escape(streaks["max_loss"])}</div>
      </div>
      <div class="metric">
        <div class="metric-label">現在の流れ</div>
        <div class="metric-value">{html.escape(streaks["current"])}</div>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <div class="panel-header">Elo推移 <span>最新: {html.escape(latest_date)}</span></div>
        {trend_html}
      </div>

      <div class="panel">
        <div class="panel-header">対戦相性 <span>2026シーズン</span></div>
        <div class="table-wrap">{matchup_html}</div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">直近10試合 <span>試合ごとのElo変化</span></div>
      <div class="table-wrap">{table_html}</div>
    </section>
  </main>
</body>
</html>
"""


def write_team_pages() -> None:
    for league_key, teams in LEAGUE_TEAMS.items():
        for team in teams:
            path = team_page_path(league_key, team)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                build_team_page_html(league_key=league_key, league_label=LEAGUE_LABELS[league_key], team=team),
                encoding="utf-8",
            )
