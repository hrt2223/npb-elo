from __future__ import annotations

import html

import pandas as pd

from .config import LEAGUE_LABELS, TEAM_COLORS


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
