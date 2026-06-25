# Implemented Features

このファイルは、現在実装されている機能の一覧です。今後あらたな機能を追加した場合は、このファイルに追記します。

## Data Collection

| feature | status | main files | output |
| --- | --- | --- | --- |
| 2026年一軍公式戦の試合結果取得 | 実装済み | `fetch_results_2026.py` | `game_results_jp_2026.csv` |
| 今日の試合予定取得 | 実装済み | `update_today_probabilities.py` | `output/today_probabilities.csv` |
| 今日の予告先発取得 | 実装済み | `update_today_probabilities.py` | `output/today_probabilities.csv` |
| 今日のスタメン取得 | 実装済み | `fetch_lineups_2026.py` | `output/today_lineups.csv` |
| セ・リーグ、パ・リーグの順位表取得 | 実装済み | `fetch_standings_2026.py` | `output/standings.csv` |

## Elo Calculation

| feature | status | main files | output |
| --- | --- | --- | --- |
| Eloレーティング計算 | 実装済み | `elo.py`, `update_daily.py` | `output/elo_final_ranking.csv`, `output/elo_by_game.csv`, `output/elo_history.csv` |
| セ・リーグだけのElo出力 | 実装済み | `update_daily.py` | `output/central/` |
| パ・リーグだけのElo出力 | 実装済み | `update_daily.py` | `output/pacific/` |
| 交流戦期間のElo出力 | 実装済み | `update_daily.py` | `output/interleague/` |
| Elo推移表の生成 | 実装済み | `make_elo_tables.py` | `output/elo_table.csv` |
| Elo推移グラフの生成 | 実装済み | `make_elo_graphs.py` | `output/elo_graph.png` |
| K値、ロジスティック関数、初期値、ホーム補正の外部設定 | 実装済み | `elo_settings.py` | Elo計算と勝率予測に反映 |

## Prediction

| feature | status | main files | output |
| --- | --- | --- | --- |
| 今日の対戦カードごとのElo勝率表示 | 実装済み | `update_today_probabilities.py`, `make_site.py` | サイトの今日の対戦予定カード |
| セ・リーグ、パ・リーグのタブ別試合予定表示 | 実装済み | `make_site.py` | `site/index.html` |
| 予告先発と勝率の同時表示 | 実装済み | `update_today_probabilities.py`, `make_site.py` | `site/index.html` |

## Site

| feature | status | main files | output |
| --- | --- | --- | --- |
| 黒基調のEloダッシュボード | 実装済み | `make_site.py`, `site_builder/dashboard.py` | `site/index.html` |
| 全体、セ・リーグ、パ・リーグ、交流戦タブ | 実装済み | `make_site.py` | `site/index.html` |
| Elo推移グラフ表示 | 実装済み | `make_site.py`, `make_elo_graphs.py` | `site/index.html` |
| 日付の縦ラインで推移確認 | 実装済み | `make_site.py` | `site/index.html` |
| Eloランキング表表示 | 実装済み | `make_site.py` | `site/index.html` |
| Elo推移表表示 | 実装済み | `make_site.py` | `site/index.html` |
| 今日の対戦予定、勝率、予告先発表示 | 実装済み | `site_builder/schedule.py` | `site/index.html` |
| 順位表表示 | 実装済み | `site_builder/standings.py` | `site/index.html` |
| スタメン表示 | 実装済み | `site_builder/schedule.py` | `site/index.html` |
| セ・リーグ、パ・リーグの各球団ページ | 実装済み | `site_builder/team_pages.py` | `site/central/`, `site/pacific/` |
| 球団ページの直近10試合成績表示 | 実装済み | `site_builder/team_pages.py` | 各球団ページ |
| 球団ページのElo上昇率表示 | 実装済み | `site_builder/team_pages.py` | 各球団ページ |
| 指定チームカラーのグラフ、カード表示 | 実装済み | `make_site.py`, `make_elo_graphs.py` | サイト、グラフPNG |

## Automation

| feature | status | main files | output |
| --- | --- | --- | --- |
| GitHub Actionsによる自動更新 | 実装済み | `.github/workflows/npb-elo-daily.yml` | GitHub上のCSV、HTML、画像 |
| 朝9時の予定、勝率、予告先発更新 | 実装済み | `.github/workflows/npb-elo-daily.yml` | `output/today_probabilities.csv`, `site/` |
| 試合前後のスタメン確認 | 実装済み | `.github/workflows/npb-elo-daily.yml`, `fetch_lineups_2026.py` | `output/today_lineups.csv` |
| 夜の試合結果更新 | 実装済み | `.github/workflows/npb-elo-daily.yml` | `game_results_jp_2026.csv`, `output/`, `site/` |
| GitHub Pages公開 | 実装済み | `index.html`, `site/` | `https://hrt2223.github.io/npb-elo/` |
| ローカルPCでの一括更新 | 実装済み | `daily_update.ps1` | ローカルのCSV、HTML、画像 |
| GitHub更新データのローカル同期 | 実装済み | `sync_from_github.ps1` | ローカルの生成データ |
| Windowsログオン時のローカル同期 | 実装済み | `install_startup_sync.ps1` | スタートアップ登録 |

## Documentation

| feature | status | file |
| --- | --- | --- |
| プロジェクト概要 | 実装済み | `docs/README.md` |
| フォルダー構成 | 実装済み | `docs/PROJECT_STRUCTURE.md` |
| 更新フローとPC同期の説明 | 実装済み | `docs/UPDATE_FLOW.md` |
| 実装済み機能一覧 | 実装済み | `docs/FEATURES.md` |

## Update Rule

新しい機能を追加したら、該当するカテゴリの表に1行追加します。

追記する内容:

| item | description |
| --- | --- |
| `feature` | 何ができるようになったか |
| `status` | `実装済み`、`一部実装`、`検討中` のいずれか |
| `main files` | 主に関係するコード |
| `output` | 生成されるCSV、HTML、画像、または表示場所 |
