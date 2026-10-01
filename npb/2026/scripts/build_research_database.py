from __future__ import annotations

"""Store NPB game totals and derive player statistics known before each game."""

import argparse
import re
import sqlite3
from dataclasses import dataclass, field
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import pandas as pd

YEAR = 2026
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE = BASE_DIR / "research" / "npb_2026_player_stats.sqlite"
SCHEDULE_URL = "https://npb.jp/games/{year}/schedule_{month:02d}_detail.html"
FULL_TEAM_NAMES = {"阪神タイガース":"阪神", "横浜DeNAベイスターズ":"DeNA", "読売ジャイアンツ":"巨人", "中日ドラゴンズ":"中日", "広島東洋カープ":"広島", "東京ヤクルトスワローズ":"ヤクルト", "福岡ソフトバンクホークス":"ソフトバンク", "北海道日本ハムファイターズ":"日本ハム", "オリックス・バファローズ":"オリックス", "東北楽天ゴールデンイーグルス":"楽天", "埼玉西武ライオンズ":"西武", "千葉ロッテマリーンズ":"ロッテ"}
PLAYER_ID_RE = re.compile(r"/players/(\d+)\.html")
SCORE_URL_RE = re.compile(r"/scores/\d{4}/\d{4}/[^\"'#?]+/")
DATE_RE = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")

@dataclass
class Cell:
    text: str = ""
    hrefs: list[str] = field(default_factory=list)

@dataclass
class Table:
    heading: str
    rows: list[list[Cell]]

class BoxParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True); self.heading_parts=[]; self.heading_depth=0; self.current_heading=""; self.tables=[]; self.table_rows=None; self.table_depth=0; self.row=None; self.cell=None; self.cell_parts=[]
    def handle_starttag(self, tag, attrs):
        if tag in {"h3", "h4"}: self.heading_depth += 1; self.heading_parts=[]
        elif tag == "table":
            if not self.table_depth: self.table_rows=[]
            self.table_depth += 1
        elif tag == "tr" and self.table_rows is not None: self.row=[]
        elif tag in {"td", "th"} and self.row is not None: self.cell=Cell(); self.cell_parts=[]
        elif tag == "a" and self.cell is not None:
            href=dict(attrs).get("href")
            if href: self.cell.hrefs.append(href)
    def handle_data(self, data):
        text=re.sub(r"\s+", " ", data).strip()
        if text:
            if self.heading_depth: self.heading_parts.append(text)
            if self.cell is not None: self.cell_parts.append(text)
    def handle_endtag(self, tag):
        if tag in {"h3", "h4"} and self.heading_depth:
            self.heading_depth -= 1
            if not self.heading_depth: self.current_heading=" ".join(self.heading_parts)
        elif tag in {"td", "th"} and self.cell is not None and self.row is not None:
            self.cell.text=" ".join(self.cell_parts).strip(); self.row.append(self.cell); self.cell=None
        elif tag == "tr" and self.row is not None and self.table_rows is not None:
            if any(cell.text for cell in self.row): self.table_rows.append(self.row)
            self.row=None
        elif tag == "table" and self.table_rows is not None:
            self.table_depth -= 1
            if not self.table_depth: self.tables.append(Table(self.current_heading, self.table_rows)); self.table_rows=None

def fetch_html(url: str, *, timeout: int = 20) -> str:
    request=Request(url, headers={"User-Agent":"Mozilla/5.0 (npb-elo-research/1.0)"})
    with urlopen(request, timeout=timeout) as response:
        raw=response.read(); declared=response.headers.get_content_charset() or "utf-8"
    decoded=raw.decode(declared, errors="replace")
    # NPB's box-score pages are currently Shift_JIS while some responses declare
    # UTF-8.  Prefer the Japanese Windows code page when that declaration yields
    # replacement characters.
    return raw.decode("cp932") if "\ufffd" in decoded else decoded

def team_name(value: str) -> str | None:
    return next((short for full, short in FULL_TEAM_NAMES.items() if full in value), None)

def player_id(cell: Cell, team: str) -> str:
    for href in cell.hrefs:
        match=PLAYER_ID_RE.search(href)
        if match: return match.group(1)
    return f"name:{team}:{cell.text}"

def integer(value: str) -> int:
    match=re.search(r"-?\d+", value.replace(",", "")); return int(match.group()) if match else 0

def event_totals(cells: list[Cell], hits: int) -> tuple[int, int, int, int, int, int]:
    text=" ".join(cell.text for cell in cells)
    home_runs=text.count("本"); triples=text.count("３") + text.count("3塁打"); doubles=text.count("２") + text.count("2塁打")
    extra=min(hits, doubles + triples + home_runs)
    if doubles + triples + home_runs != extra: doubles=max(0, extra - triples - home_runs)
    return doubles, triples, home_runs, text.count("四球") + text.count("敬遠"), text.count("死球"), text.count("犠飛")

def discover_box_urls(year: int, months: list[int]) -> list[str]:
    urls=set()
    for month in months:
        source=SCHEDULE_URL.format(year=year, month=month)
        for match in SCORE_URL_RE.finditer(fetch_html(source)):
            urls.add(urljoin(source, match.group(0)).rstrip("/") + "/box.html")
    return sorted(urls)

def parse_box(url: str, html: str):
    parser=BoxParser(); parser.feed(html)
    date_match=DATE_RE.search(re.sub(r"<[^>]+>", " ", html))
    if not date_match: return None
    date=f"{int(date_match.group(1)):04d}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
    team_order=[]
    for table in parser.tables:
        team=team_name(table.heading)
        if team and team not in team_order: team_order.append(team)
    if len(team_order) != 2: return None
    game_id=re.sub(r"\W", "_", url.replace("https://npb.jp/scores/", "").removesuffix("/box.html"))
    batting=[]; pitching=[]
    for table in parser.tables:
        team=team_name(table.heading)
        if not team or not table.rows: continue
        header=[cell.text for cell in table.rows[0]]
        if len(header) >= 7 and header[1:4] == ["守備", "選手", "打数"]:
            for row in table.rows[1:]:
                if len(row) < 7 or row[2].text in {"", "チーム計"}: continue
                if not (row[0].text.isdigit() or row[1].text in {"打", "走", "投", "捕", "指"}): continue
                ab, runs, hits, rbi=(integer(row[index].text) for index in range(3, 7))
                doubles, triples, home_runs, walks, hbp, sf=event_totals(row[7:], hits)
                batting.append((game_id, player_id(row[2], team), row[2].text, team, integer(row[0].text), ab, runs, hits, rbi, doubles, triples, home_runs, walks, hbp, sf))
    # The pitching table contains nested layout tables. pandas.read_html flattens
    # those reliably, while BoxParser above retains player-link ids for batting.
    pitcher_team_index=0
    for frame in pd.read_html(StringIO(html)):
        columns=[str(column) for column in frame.columns]
        if len(columns) < 3 or columns[1:3] != ["投手", "投球数"]: continue
        if pitcher_team_index >= len(team_order): break
        team=team_order[pitcher_team_index]; pitcher_team_index += 1; number=0
        for row in frame.fillna("").itertuples(index=False, name=None):
            if len(row) < 14 or str(row[1]) in {"", "チーム計"}: continue
            number += 1; name=str(row[1])
            pitching.append((game_id, f"name:{team}:{name}", name, team, int(number == 1), integer(str(row[2])), integer(str(row[3])), str(row[4]).replace(" ", ""), integer(str(row[5])), integer(str(row[6])), integer(str(row[7])), integer(str(row[8])), integer(str(row[9])), integer(str(row[12])), integer(str(row[13]))))
    if not batting or not pitching: return None
    return (game_id, date, team_order[0], team_order[1], url), batting, pitching

SCHEMA="""
CREATE TABLE IF NOT EXISTS games(game_id TEXT PRIMARY KEY,date TEXT NOT NULL,away_team TEXT NOT NULL,home_team TEXT NOT NULL,source_url TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS batting_game_stats(game_id TEXT,player_id TEXT,player_name TEXT,team TEXT,batting_order INTEGER,ab INTEGER,runs INTEGER,hits INTEGER,rbi INTEGER,doubles INTEGER,triples INTEGER,home_runs INTEGER,walks INTEGER,hit_by_pitch INTEGER,sacrifice_flies INTEGER,PRIMARY KEY(game_id,player_id));
CREATE TABLE IF NOT EXISTS pitching_game_stats(game_id TEXT,player_id TEXT,player_name TEXT,team TEXT,is_starter INTEGER,pitches INTEGER,batters_faced INTEGER,innings_pitched TEXT,hits_allowed INTEGER,home_runs_allowed INTEGER,walks INTEGER,hit_by_pitch INTEGER,strikeouts INTEGER,runs_allowed INTEGER,earned_runs INTEGER,PRIMARY KEY(game_id,player_id));
CREATE TABLE IF NOT EXISTS batting_pregame_stats(game_id TEXT,player_id TEXT,games_appeared_before INTEGER,ab_before INTEGER,hits_before INTEGER,doubles_before INTEGER,triples_before INTEGER,home_runs_before INTEGER,walks_before INTEGER,hit_by_pitch_before INTEGER,sacrifice_flies_before INTEGER,obp REAL,slg REAL,ops REAL,PRIMARY KEY(game_id,player_id));
CREATE TABLE IF NOT EXISTS pitching_pregame_stats(game_id TEXT,player_id TEXT,games_appeared_before INTEGER,starts_before INTEGER,outs_before INTEGER,earned_runs_before INTEGER,hits_allowed_before INTEGER,walks_before INTEGER,hit_by_pitch_before INTEGER,strikeouts_before INTEGER,era REAL,whip REAL,PRIMARY KEY(game_id,player_id));
"""

def outs(innings: str) -> int:
    match=re.fullmatch(r"(\d+)(?:\.(0|1|2))?", innings); return int(match.group(1))*3 + int(match.group(2) or 0) if match else 0

def rebuild_snapshots(db: sqlite3.Connection) -> None:
    db.execute("DELETE FROM batting_pregame_stats"); db.execute("DELETE FROM pitching_pregame_stats")
    bat={}; pit={}
    for (game_id,) in db.execute("SELECT game_id FROM games ORDER BY date, game_id"):
        batting=db.execute("SELECT * FROM batting_game_stats WHERE game_id=?", (game_id,)).fetchall(); pitching=db.execute("SELECT * FROM pitching_game_stats WHERE game_id=?", (game_id,)).fetchall()
        for row in batting:
            total=bat.setdefault(row["player_id"], dict.fromkeys(("games","ab","hits","doubles","triples","home_runs","walks","hit_by_pitch","sacrifice_flies"), 0)); den=total["ab"]+total["walks"]+total["hit_by_pitch"]+total["sacrifice_flies"]
            obp=(total["hits"]+total["walks"]+total["hit_by_pitch"])/den if den else None; slg=(total["hits"]+total["doubles"]+2*total["triples"]+3*total["home_runs"])/total["ab"] if total["ab"] else None
            db.execute("INSERT INTO batting_pregame_stats VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (game_id,row["player_id"],total["games"],total["ab"],total["hits"],total["doubles"],total["triples"],total["home_runs"],total["walks"],total["hit_by_pitch"],total["sacrifice_flies"],obp,slg,obp+slg if obp is not None and slg is not None else None))
        for row in pitching:
            total=pit.setdefault(row["player_id"], dict.fromkeys(("games","starts","outs","earned_runs","hits_allowed","walks","hit_by_pitch","strikeouts"), 0)); innings=total["outs"]/3; era=total["earned_runs"]*9/innings if innings else None; whip=(total["walks"]+total["hit_by_pitch"]+total["hits_allowed"])/innings if innings else None
            db.execute("INSERT INTO pitching_pregame_stats VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (game_id,row["player_id"],total["games"],total["starts"],total["outs"],total["earned_runs"],total["hits_allowed"],total["walks"],total["hit_by_pitch"],total["strikeouts"],era,whip))
        for row in batting:
            total=bat.setdefault(row["player_id"], dict.fromkeys(("games","ab","hits","doubles","triples","home_runs","walks","hit_by_pitch","sacrifice_flies"), 0)); total["games"] += 1
            for key in ("ab","hits","doubles","triples","home_runs","walks","hit_by_pitch","sacrifice_flies"): total[key] += row[key]
        for row in pitching:
            total=pit.setdefault(row["player_id"], dict.fromkeys(("games","starts","outs","earned_runs","hits_allowed","walks","hit_by_pitch","strikeouts"), 0)); total["games"] += 1; total["starts"] += row["is_starter"]; total["outs"] += outs(row["innings_pitched"])
            for key in ("earned_runs","hits_allowed","walks","hit_by_pitch","strikeouts"): total[key] += row[key]
    db.commit()

def store(db, parsed):
    game, batting, pitching=parsed
    with db:
        db.execute("INSERT OR REPLACE INTO games VALUES(?,?,?,?,?)", game); db.execute("DELETE FROM batting_game_stats WHERE game_id=?", (game[0],)); db.execute("DELETE FROM pitching_game_stats WHERE game_id=?", (game[0],))
        # Some official pages repeat a player in a responsive layout.  The game
        # player key is the natural id here, so retain its final complete row.
        db.executemany("INSERT OR REPLACE INTO batting_game_stats VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batting); db.executemany("INSERT OR REPLACE INTO pitching_game_stats VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", pitching)

def main() -> None:
    parser=argparse.ArgumentParser(description="Create research-only NPB game stats and pre-game player snapshots."); parser.add_argument("--database",type=Path,default=DEFAULT_DATABASE); parser.add_argument("--year",type=int,default=YEAR); parser.add_argument("--month",type=int,action="append"); parser.add_argument("--rebuild-only",action="store_true"); args=parser.parse_args()
    args.database.parent.mkdir(parents=True,exist_ok=True); db=sqlite3.connect(args.database); db.row_factory=sqlite3.Row; db.executescript(SCHEMA); stored=skipped=0
    if not args.rebuild_only:
        for url in discover_box_urls(args.year,args.month or list(range(3,13))):
            try: parsed=parse_box(url,fetch_html(url))
            except (HTTPError,URLError,TimeoutError) as exc: print(f"Skipped {url}: {exc}"); skipped += 1; continue
            if parsed: store(db,parsed); stored += 1
            else: print(f"Skipped unparseable box score: {url}"); skipped += 1
    rebuild_snapshots(db); print(f"Box scores stored: {stored}"); print(f"Skipped: {skipped}"); print(f"Games in database: {db.execute('SELECT COUNT(*) FROM games').fetchone()[0]}"); print(f"Database: {args.database}")

if __name__ == "__main__": main()
