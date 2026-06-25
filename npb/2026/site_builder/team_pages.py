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
        return "○"
    if score < opponent_score:
        return "●"
    return "△"

def result_class(result: str) -> str:
    if result == "○":
        return "win"
    if result == "●":
        return "loss"
    return "draw"

def team_recent_games(team: str, *, limit: int = 10) -> pd.DataFrame:
    by_game_path = OUTPUT_DIR / "elo_by_game.csv"
    by_game_df = read_csv(by_game_path)
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
        change_rate = (change / before) * 100 if before else 0.0
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
                "elo_change_rate": change_rate,
            }
        )

    if not records:
        return pd.DataFrame()

    recent_df = pd.DataFrame(records).sort_values(["date", "game_id"]).tail(limit).reset_index(drop=True)
    return recent_df

def team_summary(recent_df: pd.DataFrame) -> dict[str, str]:
    if recent_df.empty:
        return {"record": "0勝0敗0分", "change": "0.0", "rate": "0.00%"}

    wins = int((recent_df["result"] == "○").sum())
    losses = int((recent_df["result"] == "●").sum())
    draws = int((recent_df["result"] == "△").sum())
    first_before = float(recent_df.iloc[0]["elo_before"])
    last_after = float(recent_df.iloc[-1]["elo_after"])
    change = last_after - first_before
    rate = (change / first_before) * 100 if first_before else 0.0
    return {
        "record": f"{wins}勝{losses}敗{draws}分",
        "change": f"{change:+.1f}",
        "rate": f"{rate:+.2f}%",
    }

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
        "<tr><th>日付</th><th>勝敗</th><th>相手</th><th>場所</th><th>スコア</th>"
        "<th>試合前Elo</th><th>試合後Elo</th><th>変化</th><th>上昇率</th></tr>"
    )
    return f"<table><thead>{header}</thead><tbody>{''.join(rows)}</tbody></table>"

def build_team_page_html(*, league_key: str, league_label: str, team: str) -> str:
    recent_df = team_recent_games(team)
    summary = team_summary(recent_df)
    table_html = team_recent_table_html(recent_df)
    latest_date = str(recent_df["date"].max()) if not recent_df.empty else "-"
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
      max-width: 1120px;
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
      width: 24px;
      height: 24px;
      border-radius: 50%;
      font-weight: 900;
    }}
    .result.win {{ color: #062e18; background: #4ade80; }}
    .result.loss {{ color: #3f0b0b; background: #f87171; }}
    .result.draw {{ color: #1f2937; background: #cbd5e1; }}
    .empty {{ padding: 24px; color: var(--muted); }}
    @media (max-width: 760px) {{
      .summary {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
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
        <div class="metric-label">対象</div>
        <div class="metric-value">直近10試合</div>
      </div>
      <div class="metric">
        <div class="metric-label">勝敗</div>
        <div class="metric-value">{html.escape(summary["record"])}</div>
      </div>
      <div class="metric">
        <div class="metric-label">Elo変化</div>
        <div class="metric-value">{html.escape(summary["change"])}</div>
      </div>
      <div class="metric">
        <div class="metric-label">Elo上昇率</div>
        <div class="metric-value">{html.escape(summary["rate"])}</div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">直近10試合の勝敗結果とレーティング変化 <span style="color: var(--muted); font-weight: 600;">最新: {html.escape(latest_date)}</span></div>
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
