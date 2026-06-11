from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
SITE_DIR = BASE_DIR / "site"
TODAY_PROBABILITY_CSV = OUTPUT_DIR / "today_probabilities.csv"
STANDINGS_CSV = OUTPUT_DIR / "standings.csv"

TEAM_COLORS = {
    "阪神": "#f7d417",
    "巨人": "#f47b20",
    "広島": "#d71920",
    "中日": "#003f7f",
    "DeNA": "#00a9e0",
    "ヤクルト": "#1f9d55",
    "西武": "#7a1632",
    "ソフトバンク": "#f4c400",
    "日本ハム": "#0f5fa8",
    "ロッテ": "#111827",
    "オリックス": "#8b5a2b",
    "楽天": "#8c1d40",
}

LEAGUE_TEAMS = {
    "central": ["阪神", "巨人", "広島", "中日", "DeNA", "ヤクルト"],
    "pacific": ["西武", "ソフトバンク", "日本ハム", "ロッテ", "オリックス", "楽天"],
}

LEAGUE_LABELS = {
    "central": "セ・リーグ",
    "pacific": "パ・リーグ",
}

TEAM_SLUGS = {
    "阪神": "hanshin",
    "巨人": "giants",
    "広島": "carp",
    "中日": "dragons",
    "DeNA": "dena",
    "ヤクルト": "swallows",
    "西武": "lions",
    "ソフトバンク": "hawks",
    "日本ハム": "fighters",
    "ロッテ": "marines",
    "オリックス": "buffaloes",
    "楽天": "eagles",
}

SECTIONS = [
    {
        "key": "overall",
        "label": "全体",
        "dir": OUTPUT_DIR,
        "graph": "../output/elo_graph.png",
        "ranking": "../output/elo_final_ranking.csv",
        "table": "../output/elo_table.csv",
        "latest": "../output/elo_latest.txt",
    },
    {
        "key": "central",
        "label": "セ・リーグ",
        "dir": OUTPUT_DIR / "central",
        "graph": "../output/central/elo_graph.png",
        "ranking": "../output/central/elo_final_ranking.csv",
        "table": "../output/central/elo_table.csv",
        "latest": "../output/central/elo_latest.txt",
    },
    {
        "key": "pacific",
        "label": "パ・リーグ",
        "dir": OUTPUT_DIR / "pacific",
        "graph": "../output/pacific/elo_graph.png",
        "ranking": "../output/pacific/elo_final_ranking.csv",
        "table": "../output/pacific/elo_table.csv",
        "latest": "../output/pacific/elo_latest.txt",
    },
    {
        "key": "interleague",
        "label": "交流戦",
        "dir": OUTPUT_DIR / "interleague",
        "graph": "../output/interleague/elo_graph.png",
        "ranking": "../output/interleague/elo_final_ranking.csv",
        "table": "../output/interleague/elo_table.csv",
        "latest": "../output/interleague/elo_latest.txt",
    },
]


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig")


def format_number(value) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


def df_to_table(df: pd.DataFrame, *, max_rows: int | None = None) -> str:
    if df.empty:
        return '<div class="empty">データがありません</div>'

    if max_rows is not None:
        df = df.tail(max_rows)

    header = "".join(f"<th>{html.escape(str(col))}</th>" for col in df.columns)
    rows = []
    for _, row in df.iterrows():
        cells = "".join(f"<td>{html.escape(format_number(row[col]))}</td>" for col in df.columns)
        rows.append(f"<tr>{cells}</tr>")

    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def today_probabilities_html(df: pd.DataFrame) -> str:
    if df.empty:
        return '<div class="empty">今日の対戦予定はありません</div>'

    date = str(df.iloc[0].get("date", "-"))
    cards = []
    for _, row in df.iterrows():
        home = str(row["home"])
        away = str(row["away"])
        home_color = TEAM_COLORS.get(home, "#38bdf8")
        away_color = TEAM_COLORS.get(away, "#94a3b8")
        home_prob = float(row["home_win_probability"])
        away_prob = float(row["away_win_probability"])
        status = str(row.get("status", "予定"))
        venue = " / ".join(
            value
            for value in [str(row.get("start_time", "")).strip(), str(row.get("stadium", "")).strip()]
            if value
        )

        cards.append(
            f"""
            <article class="schedule-card">
              <div class="schedule-meta">
                <span>{html.escape(str(row.get("game_type", "")))}</span>
                <span>{html.escape(status)}</span>
              </div>
              <div class="schedule-teams">
                <div class="team-name"><span class="team-dot" style="background:{html.escape(home_color)}"></span>{html.escape(home)}</div>
                <div class="versus">vs</div>
                <div class="team-name is-away"><span class="team-dot" style="background:{html.escape(away_color)}"></span>{html.escape(away)}</div>
              </div>
              <div class="schedule-venue">{html.escape(venue)}</div>
              <div class="probability-row">
                <span>{home_prob:.1f}%</span>
                <div class="probability-bar" aria-label="{html.escape(home)} 勝率 {home_prob:.1f}% / {html.escape(away)} 勝率 {away_prob:.1f}%">
                  <span class="home-prob" style="width:{home_prob:.1f}%; background:{html.escape(home_color)}"></span>
                  <span class="away-prob" style="width:{away_prob:.1f}%; background:{html.escape(away_color)}"></span>
                </div>
                <span>{away_prob:.1f}%</span>
              </div>
              <div class="elo-row">
                <span>Elo {float(row["home_elo"]):.1f}</span>
                <span>Elo {float(row["away_elo"]):.1f}</span>
              </div>
            </article>
            """
        )

    return (
        f'<div class="schedule-date">対象日: {html.escape(date)}</div>'
        f'<div class="schedule-grid">{"".join(cards)}</div>'
    )


def format_win_pct(value) -> str:
    if pd.isna(value):
        return ""
    try:
        return f"{float(value):.3f}".lstrip("0")
    except (TypeError, ValueError):
        return str(value)


def standings_table_html(df: pd.DataFrame, *, league_key: str) -> str:
    if df.empty:
        return '<div class="empty">順位表データがありません</div>'

    league_df = df[df["league"] == league_key].sort_values("rank")
    if league_df.empty:
        return '<div class="empty">順位表データがありません</div>'

    league_label = LEAGUE_LABELS[league_key]
    source_date = str(league_df.iloc[0].get("source_date", "-"))
    rows = []
    for _, row in league_df.iterrows():
        team = str(row["team"])
        color = TEAM_COLORS.get(team, "#38bdf8")
        rows.append(
            "<tr>"
            f"<td>{int(row['rank'])}</td>"
            f'<td class="standings-team"><span class="team-dot" style="background:{html.escape(color)}"></span>{html.escape(team)}</td>'
            f"<td>{int(row['games'])}</td>"
            f"<td>{int(row['wins'])}</td>"
            f"<td>{int(row['losses'])}</td>"
            f"<td>{int(row['draws'])}</td>"
            f"<td>{html.escape(format_win_pct(row['win_pct']))}</td>"
            f"<td>{html.escape(str(row['games_behind']))}</td>"
            "</tr>"
        )

    return f"""
    <section class="standings-table">
      <div class="standings-title">
        <span>{html.escape(league_label)}</span>
        <span>{html.escape(source_date)} 現在</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>順位</th><th>球団</th><th>試合</th><th>勝</th><th>敗</th><th>分</th><th>勝率</th><th>差</th></tr>
          </thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
    </section>
    """


def standings_for_section_html(df: pd.DataFrame, *, section_key: str) -> str:
    if df.empty:
        return '<div class="empty">順位表データがありません</div>'

    league_keys = [section_key] if section_key in LEAGUE_LABELS else ["central", "pacific"]
    tables = [standings_table_html(df, league_key=league_key) for league_key in league_keys]

    if not tables:
        return '<div class="empty">順位表データがありません</div>'

    return f'<div class="standings-grid">{"".join(tables)}</div>'


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
    for _, row in recent_df.iterrows():
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


def read_latest_text(path: Path) -> dict[str, str]:
    if not path.exists():
        return {"updated": "-", "period": "-", "games": "-"}

    values = {"updated": "-", "period": "-", "games": "-"}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Updated at:"):
            values["updated"] = line.replace("Updated at:", "").strip()
        elif line.startswith("Period:"):
            values["period"] = line.replace("Period:", "").strip()
        elif line.startswith("Games:"):
            values["games"] = line.replace("Games:", "").strip()
    return values


def build_section_payload(section: dict[str, object]) -> dict[str, str]:
    section_dir = Path(section["dir"])
    ranking_df = read_csv(section_dir / "elo_final_ranking.csv")
    table_df = read_csv(section_dir / "elo_table.csv")
    latest = read_latest_text(section_dir / "elo_latest.txt")

    latest_date = "-"
    if not table_df.empty and "date" in table_df.columns:
        latest_date = str(table_df["date"].max())

    chart_df = table_df.copy()
    if not chart_df.empty:
        chart_df = chart_df.where(pd.notna(chart_df), None)

    return {
        "key": str(section["key"]),
        "label": str(section["label"]),
        "graph": str(section["graph"]).replace("\\", "/"),
        "rankingLink": str(section["ranking"]).replace("\\", "/"),
        "tableLink": str(section["table"]).replace("\\", "/"),
        "latestLink": str(section["latest"]).replace("\\", "/"),
        "rankingHtml": df_to_table(ranking_df),
        "tableHtml": df_to_table(table_df, max_rows=10),
        "updated": latest["updated"],
        "period": latest["period"],
        "games": latest["games"],
        "latestDate": latest_date,
        "chartData": chart_df.to_dict(orient="records") if not chart_df.empty else [],
        "teamLinksHtml": build_team_links_html(str(section["key"])),
        "standingsHtml": standings_for_section_html(read_csv(STANDINGS_CSV), section_key=str(section["key"])),
    }


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


def build_html(payload: list[dict[str, str]]) -> str:
    data_json = json.dumps(payload, ensure_ascii=False)
    colors_json = json.dumps(TEAM_COLORS, ensure_ascii=False)
    first = payload[0]
    today_html = today_probabilities_html(read_csv(TODAY_PROBABILITY_CSV))
    tabs = "".join(
        f'<button class="tab{" is-active" if item["key"] == first["key"] else ""}" data-key="{item["key"]}">{html.escape(item["label"])}</button>'
        for item in payload
    )

    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>2026 NPB Elo Dashboard</title>
  <style>
    :root {{
      --bg: #07090d;
      --surface: #10141d;
      --surface-2: #151b26;
      --ink: #edf2f7;
      --muted: #9aa4b2;
      --line: #252d3a;
      --line-strong: #374151;
      --accent: #38bdf8;
      --accent-dark: #7dd3fc;
      --glow: rgba(56, 189, 248, 0.22);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Yu Gothic", "Meiryo", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      background:
        radial-gradient(circle at 50% -20%, rgba(56, 189, 248, 0.12), transparent 34%),
        linear-gradient(180deg, #0b111a 0%, var(--bg) 38%, #050608 100%);
      color: var(--ink);
      min-height: 100vh;
    }}
    header {{
      border-bottom: 1px solid rgba(125, 211, 252, 0.18);
      background: rgba(8, 12, 18, 0.88);
      backdrop-filter: blur(14px);
      box-shadow: 0 16px 50px rgba(0, 0, 0, 0.28);
    }}
    .header-inner {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 20px 24px 16px;
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 20px;
    }}
    h1 {{
      margin: 0;
      font-size: 25px;
      line-height: 1.2;
      letter-spacing: 0;
      color: #f8fafc;
    }}
    .updated {{
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 20px 24px 32px;
    }}
    .tabs {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 16px;
    }}
    .tab {{
      border: 1px solid var(--line);
      background: rgba(16, 20, 29, 0.86);
      color: var(--ink);
      border-radius: 6px;
      padding: 9px 14px;
      font: inherit;
      cursor: pointer;
      transition: border-color 160ms ease, background 160ms ease, box-shadow 160ms ease;
    }}
    .tab:hover {{
      border-color: rgba(125, 211, 252, 0.55);
      background: #151b26;
    }}
    .tab.is-active {{
      background: #0f3144;
      border-color: var(--accent);
      color: #e0f7ff;
      box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.16), 0 10px 28px var(--glow);
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }}
    .metric {{
      background: linear-gradient(180deg, rgba(21, 27, 38, 0.96), rgba(12, 16, 24, 0.96));
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px 16px;
      min-height: 76px;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
    }}
    .metric-label {{
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }}
    .metric-value {{
      font-size: 18px;
      font-weight: 700;
      line-height: 1.3;
      overflow-wrap: anywhere;
      color: #f8fafc;
    }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 1.7fr) minmax(320px, 0.9fr);
      gap: 16px;
      align-items: start;
    }}
    .panel {{
      background: rgba(16, 20, 29, 0.94);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 18px 55px rgba(0, 0, 0, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.035);
    }}
    .panel-header {{
      padding: 13px 16px;
      border-bottom: 1px solid var(--line);
      background: rgba(21, 27, 38, 0.72);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}
    .panel-title {{
      font-size: 15px;
      font-weight: 700;
      color: #f8fafc;
    }}
    .links {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      font-size: 13px;
    }}
    a {{
      color: var(--accent-dark);
      text-decoration: none;
      font-weight: 600;
    }}
    a:hover {{ text-decoration: underline; }}
    .schedule-date {{
      color: var(--muted);
      font-size: 13px;
      padding: 12px 16px 0;
    }}
    .schedule-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      padding: 12px;
    }}
    .schedule-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: linear-gradient(180deg, #0d131d 0%, #090d14 100%);
      padding: 13px;
      min-width: 0;
    }}
    .schedule-meta {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 11px;
    }}
    .schedule-teams {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
    }}
    .team-name {{
      display: flex;
      align-items: center;
      gap: 7px;
      min-width: 0;
      font-weight: 800;
      color: #f8fafc;
    }}
    .team-name.is-away {{
      justify-content: flex-end;
    }}
    .versus {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
    }}
    .schedule-venue {{
      color: #cbd5e1;
      font-size: 12px;
      min-height: 18px;
      margin-bottom: 12px;
    }}
    .probability-row {{
      display: grid;
      grid-template-columns: 44px minmax(96px, 1fr) 44px;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      font-weight: 800;
      color: #e5edf7;
    }}
    .probability-row span:last-child {{
      text-align: right;
    }}
    .probability-bar {{
      display: flex;
      height: 9px;
      border-radius: 999px;
      background: #1f2937;
      overflow: hidden;
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.06);
    }}
    .probability-bar span {{
      display: block;
      height: 100%;
      flex: 0 0 auto;
    }}
    .probability-bar .home-prob {{
      border-radius: 999px 0 0 999px;
    }}
    .probability-bar .away-prob {{
      border-radius: 0 999px 999px 0;
    }}
    .elo-row {{
      display: flex;
      justify-content: space-between;
      color: var(--muted);
      font-size: 11px;
      margin-top: 8px;
    }}
    .standings-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      padding: 12px;
    }}
    .standings-table {{
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: #0b1018;
    }}
    .standings-title {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 11px 12px;
      background: #111827;
      border-bottom: 1px solid var(--line);
      color: #f8fafc;
      font-weight: 800;
      font-size: 13px;
    }}
    .standings-title span:last-child {{
      color: var(--muted);
      font-weight: 600;
      font-size: 12px;
      white-space: nowrap;
    }}
    .standings-team {{
      display: flex;
      align-items: center;
      gap: 8px;
      text-align: left;
      font-weight: 800;
      color: #f8fafc;
    }}
    .graph-wrap {{
      padding: 12px;
    }}
    .chart {{
      width: 100%;
      height: min(62vh, 620px);
      min-height: 360px;
      display: block;
      border: 1px solid var(--line-strong);
      border-radius: 6px;
      background: #090d14;
    }}
    .tooltip {{
      position: fixed;
      z-index: 10;
      max-width: min(320px, calc(100vw - 24px));
      background: rgba(10, 14, 21, 0.96);
      color: var(--ink);
      border: 1px solid rgba(125, 211, 252, 0.28);
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.42);
      border-radius: 8px;
      padding: 10px 12px;
      pointer-events: none;
      display: none;
      font-size: 12px;
    }}
    .tooltip-title {{
      font-weight: 700;
      margin-bottom: 6px;
    }}
    .tooltip-row {{
      display: grid;
      grid-template-columns: 10px 1fr auto;
      gap: 7px;
      align-items: center;
      margin: 3px 0;
    }}
    .swatch {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      border: 1px solid rgba(0, 0, 0, 0.15);
    }}
    .team-links {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      padding: 12px;
    }}
    .team-link {{
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 42px;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: #0b1018;
      color: #edf2f7;
    }}
    .team-link:hover {{
      border-color: rgba(125, 211, 252, 0.45);
      background: #111827;
      text-decoration: none;
    }}
    .team-dot {{
      width: 11px;
      height: 11px;
      border-radius: 50%;
      box-shadow: 0 0 18px currentColor;
      flex: 0 0 auto;
    }}
    .result {{
      display: inline-grid;
      place-items: center;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      font-weight: 800;
    }}
    .result.win {{
      color: #062e18;
      background: #4ade80;
    }}
    .result.loss {{
      color: #3f0b0b;
      background: #f87171;
    }}
    .result.draw {{
      color: #1f2937;
      background: #cbd5e1;
    }}
    .table-wrap {{
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      white-space: nowrap;
      color: #dbe3ee;
    }}
    th, td {{
      padding: 9px 10px;
      border-bottom: 1px solid #202733;
      text-align: right;
    }}
    th {{
      background: #151b26;
      color: #cbd5e1;
      font-weight: 700;
    }}
    tbody tr:hover {{
      background: rgba(56, 189, 248, 0.06);
    }}
    th:first-child, td:first-child {{
      text-align: left;
    }}
    .stack {{
      display: grid;
      gap: 16px;
    }}
    .empty {{
      padding: 24px;
      color: var(--muted);
    }}
    @media (max-width: 900px) {{
      .header-inner {{
        display: block;
      }}
      .updated {{
        margin-top: 8px;
        white-space: normal;
      }}
      .summary {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .layout {{
        grid-template-columns: 1fr;
      }}
      .schedule-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .standings-grid {{
        grid-template-columns: 1fr;
      }}
    }}
    @media (max-width: 560px) {{
      main, .header-inner {{
        padding-left: 14px;
        padding-right: 14px;
      }}
      .summary {{
        grid-template-columns: 1fr;
      }}
      h1 {{ font-size: 21px; }}
      .chart {{
        min-height: 300px;
      }}
      .schedule-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="header-inner">
      <h1>2026 NPB Elo Dashboard</h1>
      <div class="updated" id="pageUpdated">更新日時: {html.escape(first["updated"])}</div>
    </div>
  </header>
  <main>
    <nav class="tabs" aria-label="表示切り替え">
      {tabs}
    </nav>

    <section class="summary">
      <div class="metric">
        <div class="metric-label">表示</div>
        <div class="metric-value" id="metricLabel">{html.escape(first["label"])}</div>
      </div>
      <div class="metric">
        <div class="metric-label">最新日</div>
        <div class="metric-value" id="metricLatestDate">{html.escape(first["latestDate"])}</div>
      </div>
      <div class="metric">
        <div class="metric-label">対象試合数</div>
        <div class="metric-value" id="metricGames">{html.escape(first["games"])}</div>
      </div>
      <div class="metric">
        <div class="metric-label">対象期間</div>
        <div class="metric-value" id="metricPeriod">{html.escape(first["period"])}</div>
      </div>
    </section>

    <section class="panel" style="margin-bottom: 16px;">
      <div class="panel-header">
        <div class="panel-title">順位表</div>
        <div class="links">
          <a href="../output/standings.csv">CSV</a>
        </div>
      </div>
      <div id="standingsContent">{first["standingsHtml"]}</div>
    </section>

    <section class="panel" style="margin-bottom: 16px;">
      <div class="panel-header">
        <div class="panel-title">今日の対戦予定と勝率</div>
        <div class="links">
          <a href="../output/today_probabilities.csv">CSV</a>
        </div>
      </div>
      {today_html}
    </section>

    <section class="layout">
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">Elo 推移グラフ</div>
          <div class="links">
            <a id="graphLink" href="{html.escape(first["graph"])}">画像を開く</a>
            <a id="tableLink" href="{html.escape(first["tableLink"])}">推移表CSV</a>
          </div>
        </div>
        <div class="graph-wrap">
          <svg class="chart" id="chart" role="img" aria-label="Elo 推移グラフ"></svg>
        </div>
      </div>

      <div class="stack">
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">最新ランキング</div>
            <div class="links">
              <a id="rankingLink" href="{html.escape(first["rankingLink"])}">CSV</a>
              <a id="latestLink" href="{html.escape(first["latestLink"])}">サマリ</a>
            </div>
          </div>
          <div class="table-wrap" id="rankingTable">{first["rankingHtml"]}</div>
        </div>

        <div class="panel" id="teamLinksPanel" style="display: none;">
          <div class="panel-header">
            <div class="panel-title">球団ページ</div>
          </div>
          <div id="teamLinks"></div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">直近10日 Elo 推移</div>
          </div>
          <div class="table-wrap" id="historyTable">{first["tableHtml"]}</div>
        </div>
      </div>
    </section>
  </main>
  <div class="tooltip" id="tooltip"></div>

  <script>
    const sections = {data_json};
    const teamColors = {colors_json};
    const byKey = new Map(sections.map((item) => [item.key, item]));
    let activeKey = "{first["key"]}";

    const fallbackColors = [
      "#0068b7", "#c43d3d", "#1f8a5b", "#7c3aed", "#d97706", "#475467",
      "#0e7490", "#be123c", "#4d7c0f", "#4338ca", "#a16207", "#525252"
    ];

    function svgEl(name, attrs = {{}}, text = "") {{
      const node = document.createElementNS("http://www.w3.org/2000/svg", name);
      Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
      if (text) node.textContent = text;
      return node;
    }}

    function teamColor(team, index) {{
      return teamColors[team] || fallbackColors[index % fallbackColors.length];
    }}

    function valueAt(row, team) {{
      const value = row[team];
      if (value === null || value === undefined || value === "") return null;
      const number = Number(value);
      return Number.isFinite(number) ? number : null;
    }}

    function drawChart(item) {{
      const svg = document.getElementById("chart");
      const tooltip = document.getElementById("tooltip");
      svg.innerHTML = "";

      const rows = item.chartData || [];
      if (!rows.length) {{
        svg.appendChild(svgEl("text", {{ x: "50%", y: "50%", "text-anchor": "middle", fill: "#667085" }}, "データがありません"));
        return;
      }}

      const width = 1120;
      const height = 560;
      const margin = {{ top: 32, right: 24, bottom: 54, left: 56 }};
      const innerWidth = width - margin.left - margin.right;
      const innerHeight = height - margin.top - margin.bottom;
      svg.setAttribute("viewBox", `0 0 ${{width}} ${{height}}`);

      const teams = Object.keys(rows[0]).filter((key) => key !== "date");
      const values = [];
      rows.forEach((row) => {{
        teams.forEach((team) => {{
          const value = valueAt(row, team);
          if (value !== null) values.push(value);
        }});
      }});

      const minValue = Math.floor((Math.min(...values) - 15) / 10) * 10;
      const maxValue = Math.ceil((Math.max(...values) + 15) / 10) * 10;
      const x = (index) => margin.left + (rows.length <= 1 ? innerWidth / 2 : (index / (rows.length - 1)) * innerWidth);
      const y = (value) => margin.top + ((maxValue - value) / (maxValue - minValue)) * innerHeight;

      const plot = svgEl("g");
      svg.appendChild(plot);

      for (let i = 0; i <= 5; i += 1) {{
        const value = minValue + ((maxValue - minValue) / 5) * i;
        const yy = y(value);
        plot.appendChild(svgEl("line", {{ x1: margin.left, x2: width - margin.right, y1: yy, y2: yy, stroke: "#1f2937", "stroke-width": 1 }}));
        plot.appendChild(svgEl("text", {{ x: margin.left - 10, y: yy + 4, "text-anchor": "end", fill: "#94a3b8", "font-size": 12 }}, value.toFixed(0)));
      }}

      const dateTickStep = Math.max(1, Math.ceil(rows.length / 8));
      rows.forEach((row, index) => {{
        if (index % dateTickStep !== 0 && index !== rows.length - 1) return;
        const xx = x(index);
        plot.appendChild(svgEl("line", {{ x1: xx, x2: xx, y1: margin.top, y2: height - margin.bottom, stroke: "#151c27", "stroke-width": 1 }}));
        plot.appendChild(svgEl("text", {{ x: xx, y: height - 22, "text-anchor": "middle", fill: "#94a3b8", "font-size": 11 }}, row.date.slice(5)));
      }});

      teams.forEach((team, teamIndex) => {{
        let path = "";
        let started = false;
        rows.forEach((row, rowIndex) => {{
          const value = valueAt(row, team);
          if (value === null) {{
            started = false;
            return;
          }}
          const command = started ? "L" : "M";
          path += `${{command}} ${{x(rowIndex).toFixed(2)}} ${{y(value).toFixed(2)}} `;
          started = true;
        }});
        if (path) {{
          plot.appendChild(svgEl("path", {{
            d: path,
            fill: "none",
            stroke: teamColor(team, teamIndex),
            "stroke-width": 3,
            "stroke-linejoin": "round",
            "stroke-linecap": "round"
          }}));
        }}
      }});

      plot.appendChild(svgEl("line", {{ x1: margin.left, x2: width - margin.right, y1: height - margin.bottom, y2: height - margin.bottom, stroke: "#475569", "stroke-width": 1 }}));
      plot.appendChild(svgEl("line", {{ x1: margin.left, x2: margin.left, y1: margin.top, y2: height - margin.bottom, stroke: "#475569", "stroke-width": 1 }}));

      const cursor = svgEl("line", {{ y1: margin.top, y2: height - margin.bottom, stroke: "#e2e8f0", "stroke-width": 1.5, "stroke-dasharray": "5 4", opacity: 0 }});
      plot.appendChild(cursor);
      const pointLayer = svgEl("g");
      plot.appendChild(pointLayer);
      const hit = svgEl("rect", {{ x: margin.left, y: margin.top, width: innerWidth, height: innerHeight, fill: "transparent" }});
      svg.appendChild(hit);

      function showAt(event) {{
        const rect = svg.getBoundingClientRect();
        const px = ((event.clientX - rect.left) / rect.width) * width;
        const ratio = Math.max(0, Math.min(1, (px - margin.left) / innerWidth));
        const index = Math.round(ratio * (rows.length - 1));
        const row = rows[index];
        const xx = x(index);

        cursor.setAttribute("x1", xx);
        cursor.setAttribute("x2", xx);
        cursor.setAttribute("opacity", "1");
        pointLayer.innerHTML = "";

        const rowsHtml = teams
          .map((team, teamIndex) => [team, valueAt(row, team), teamColor(team, teamIndex)])
          .filter(([, value]) => value !== null)
          .sort((a, b) => b[1] - a[1])
          .map(([team, value, color]) => {{
            pointLayer.appendChild(svgEl("circle", {{ cx: xx, cy: y(value), r: 4.5, fill: color, stroke: "#fff", "stroke-width": 1.5 }}));
            return `<div class="tooltip-row"><span class="swatch" style="background:${{color}}"></span><span>${{team}}</span><strong>${{value.toFixed(1)}}</strong></div>`;
          }})
          .join("");

        tooltip.innerHTML = `<div class="tooltip-title">${{row.date}}</div>${{rowsHtml}}`;
        tooltip.style.display = "block";
        const left = Math.min(window.innerWidth - tooltip.offsetWidth - 12, event.clientX + 14);
        const top = Math.min(window.innerHeight - tooltip.offsetHeight - 12, event.clientY + 14);
        tooltip.style.left = `${{Math.max(12, left)}}px`;
        tooltip.style.top = `${{Math.max(12, top)}}px`;
      }}

      function hide() {{
        cursor.setAttribute("opacity", "0");
        pointLayer.innerHTML = "";
        tooltip.style.display = "none";
      }}

      hit.addEventListener("mousemove", showAt);
      hit.addEventListener("mouseleave", hide);
      hit.addEventListener("touchstart", (event) => showAt(event.touches[0]), {{ passive: true }});
      hit.addEventListener("touchmove", (event) => showAt(event.touches[0]), {{ passive: true }});
    }}

    function setSection(key) {{
      const item = byKey.get(key);
      if (!item) return;
      activeKey = key;

      document.querySelectorAll(".tab").forEach((tab) => {{
        tab.classList.toggle("is-active", tab.dataset.key === key);
      }});

      document.getElementById("pageUpdated").textContent = `更新日時: ${{item.updated}}`;
      document.getElementById("metricLabel").textContent = item.label;
      document.getElementById("metricLatestDate").textContent = item.latestDate;
      document.getElementById("metricGames").textContent = item.games;
      document.getElementById("metricPeriod").textContent = item.period;

      document.getElementById("graphLink").href = item.graph;
      document.getElementById("rankingLink").href = item.rankingLink;
      document.getElementById("tableLink").href = item.tableLink;
      document.getElementById("latestLink").href = item.latestLink;
      document.getElementById("rankingTable").innerHTML = item.rankingHtml;
      document.getElementById("standingsContent").innerHTML = item.standingsHtml;
      document.getElementById("historyTable").innerHTML = item.tableHtml;
      document.getElementById("teamLinks").innerHTML = item.teamLinksHtml || "";
      document.getElementById("teamLinksPanel").style.display = item.teamLinksHtml ? "" : "none";
      drawChart(item);
    }}

    document.querySelectorAll(".tab").forEach((tab) => {{
      tab.addEventListener("click", () => setSection(tab.dataset.key));
    }});
    window.addEventListener("resize", () => drawChart(byKey.get(activeKey)));
    drawChart(byKey.get(activeKey));
  </script>
</body>
</html>
"""


def main() -> None:
    payload = [build_section_payload(section) for section in SECTIONS]
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    index_path = SITE_DIR / "index.html"
    index_path.write_text(build_html(payload), encoding="utf-8")
    print(f"Saved: {index_path}")
    write_team_pages()
    print("Saved team pages")


if __name__ == "__main__":
    main()
