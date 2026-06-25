from __future__ import annotations

import html

import pandas as pd

from .config import LEAGUE_LABELS, TEAM_COLORS


def schedule_section_df(df: pd.DataFrame, *, section_key: str) -> pd.DataFrame:
    if df.empty:
        return df
    if section_key in LEAGUE_LABELS and "game_type" in df.columns:
        return df[df["game_type"] == LEAGUE_LABELS[section_key]].copy()
    if section_key == "interleague" and "game_type" in df.columns:
        return df[df["game_type"] == "交流戦"].copy()
    return df

def lineup_html(lineup_df: pd.DataFrame, *, date: str, home: str, away: str) -> str:
    if lineup_df.empty:
        return '<div class="lineup-empty">スタメン未発表</div>'

    game_key = f"{date}_{home}_{away}"
    game_df = lineup_df[(lineup_df["game_key"] == game_key) & (lineup_df["status"] == "available")].copy()
    if game_df.empty:
        return '<div class="lineup-empty">スタメン未発表</div>'

    columns = []
    for team in [home, away]:
        team_df = game_df[game_df["team"] == team].copy()
        if team_df.empty:
            continue
        team_df["batting_order"] = pd.to_numeric(team_df["batting_order"], errors="coerce")
        team_df = team_df.sort_values("batting_order")
        items = []
        for _, row in team_df.iterrows():
            order = int(row["batting_order"])
            position = str(row.get("position", ""))
            player = str(row.get("player_name", ""))
            items.append(
                f'<li><span>{order}</span><span>{html.escape(position)}</span><strong>{html.escape(player)}</strong></li>'
            )
        columns.append(
            f"""
            <div class="lineup-team">
              <div class="lineup-team-title">{html.escape(team)}</div>
              <ol class="lineup-list">{"".join(items)}</ol>
            </div>
            """
        )

    if not columns:
        return '<div class="lineup-empty">スタメン未発表</div>'
    return f'<div class="lineup-box">{"".join(columns)}</div>'

def probable_starter_html(row: pd.Series) -> str:
    home = str(row["home"])
    away = str(row["away"])
    home_starter = str(row.get("home_probable_starter", "") or "").strip()
    away_starter = str(row.get("away_probable_starter", "") or "").strip()

    if not home_starter and not away_starter:
        return '<div class="starter-row"><span>予告先発</span><strong>未発表</strong></div>'

    home_text = home_starter or "未発表"
    away_text = away_starter or "未発表"
    return (
        '<div class="starter-row">'
        '<span>予告先発</span>'
        f'<strong>{html.escape(home)}: {html.escape(home_text)} / {html.escape(away)}: {html.escape(away_text)}</strong>'
        "</div>"
    )

def today_probabilities_html(
    df: pd.DataFrame,
    *,
    lineup_df: pd.DataFrame,
    section_key: str = "overall",
) -> str:
    if df.empty:
        return '<div class="empty">今日の対戦予定はありません</div>'

    date = str(df.iloc[0].get("date", "-"))
    df = schedule_section_df(df, section_key=section_key)
    if df.empty:
        return (
            f'<div class="schedule-date">対象日: {html.escape(date)}</div>'
            '<div class="empty">このタブの今日の対戦予定はありません</div>'
        )

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
        probable_starters = probable_starter_html(row)
        lineups = lineup_html(lineup_df, date=str(row["date"]), home=home, away=away)

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
              {probable_starters}
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
              {lineups}
            </article>
            """
        )

    return (
        f'<div class="schedule-date">対象日: {html.escape(date)}</div>'
        f'<div class="schedule-grid">{"".join(cards)}</div>'
    )
