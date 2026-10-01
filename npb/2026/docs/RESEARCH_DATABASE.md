# 研究用選手成績データベース

`scripts/build_research_database.py` は、Eloサイト本体とは分離したSQLiteデータベースを作る。

```powershell
cd C:\2026\kenkyu\elo\npb\2026
python scripts\build_research_database.py
```

保存先は `research/npb_2026_player_stats.sqlite`。NPB公式の試合別投打成績を保存し、全試合を日時順に処理して、各試合の**開始前**の選手成績を作る。既存の生データだけから再計算する場合は次を使う。

```powershell
python scripts\build_research_database.py --rebuild-only
```

| table | 内容 |
| --- | --- |
| `batting_game_stats` | 試合別の打者成績（AB、H、2B、3B、HR、BB、HBP、SFなど） |
| `pitching_game_stats` | 試合別の投手成績と実先発フラグ |
| `batting_pregame_stats` | 試合直前の打者成績、OBP、SLG、OPS、出場試合数 |
| `pitching_pregame_stats` | 試合直前の投手成績、ERA、WHIP、登板数・先発数 |

`games_appeared_before` は、その選手が当該試合の開始前までに出場した試合数。打者は打撃成績表に掲載された試合、投手は登板試合を数える。

```text
OBP = (H + BB + HBP) / (AB + BB + HBP + SF)
SLG = (H + 2B + 2×3B + 3×HR) / AB
OPS = OBP + SLG
```

各試合のスナップショットを書いた後に当該試合を累積へ反映するため、後日の成績は混ざらない。

## 球団別CSV

DBは1つに保ったまま、閲覧用に12球団別のCSVを出力できる。

```powershell
python scripts\export_research_team_data.py
```

出力先は `research/team_exports/`。球団ごとに `球団名_batting_pregame.csv` と `球団名_pitching_pregame.csv` が作られる。
