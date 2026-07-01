from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
SITE_DIR = BASE_DIR / "site"
GAME_RESULTS_CSV = BASE_DIR / "game_results_jp_2026.csv"
TODAY_PROBABILITY_CSV = OUTPUT_DIR / "today_probabilities.csv"
TODAY_LINEUPS_CSV = OUTPUT_DIR / "today_lineups.csv"
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
