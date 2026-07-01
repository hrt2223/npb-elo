from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import GAME_RESULTS_CSV, STANDINGS_CSV, TODAY_LINEUPS_CSV, TODAY_PROBABILITY_CSV, UPCOMING_SCHEDULE_CSV
from .schedule import today_probabilities_html, upcoming_schedule_html
from .standings import standings_for_section_html
from .tables import df_to_table, read_csv, read_latest_text
from .team_pages import build_team_links_html


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

    today_probability_df = read_csv(TODAY_PROBABILITY_CSV)
    upcoming_schedule_df = read_csv(UPCOMING_SCHEDULE_CSV)

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
        "scheduleHtml": today_probabilities_html(
            today_probability_df,
            lineup_df=read_csv(TODAY_LINEUPS_CSV),
            results_df=read_csv(GAME_RESULTS_CSV),
            section_key=str(section["key"]),
        ),
        "scheduleTomorrowHtml": upcoming_schedule_html(
            upcoming_schedule_df,
            today_df=today_probability_df,
            section_key=str(section["key"]),
            window="tomorrow",
        ),
        "scheduleWeekHtml": upcoming_schedule_html(
            upcoming_schedule_df,
            today_df=today_probability_df,
            section_key=str(section["key"]),
            window="week",
        ),
    }
