# Implemented Features

このファイルは、`npb/2026` で現在実装されている機能の一覧です。
新しい機能を追加した場合は、該当するカテゴリの表へ1行追加してください。

## Data Collection

| feature | status | main files | output |
| --- | --- | --- | --- |
| 2026年一軍公式戦の試合結果取得 | 実装済み | `scripts/fetch_results_2026.py` | `game_results_jp_2026.csv` |
| 月次結果の再取得と既存CSVへの反映 | 実装済み | `scripts/fetch_results_2026.py` | `game_results_jp_2026.csv` |
| 中止・未成立試合を結果CSVへ入れない制御 | 実装済み | `scripts/fetch_results_2026.py` | `game_results_jp_2026.csv` |
| 今日の試合予定取得 | 実装済み | `scripts/update_today_probabilities.py` | `output/today_probabilities.csv` |
| 今日の予告先発取得 | 実装済み | `scripts/update_today_probabilities.py` | `output/today_probabilities.csv` |
| 月別日程ページによる当日予告先発の補完 | 実装済み | `scripts/update_today_probabilities.py` | `output/today_probabilities.csv` |
| 試合ステータスの中止・終了反映 | 実装済み | `scripts/update_today_probabilities.py`, `site_builder/schedule.py` | `output/today_probabilities.csv`, `site/index.html` |
| 今日のスタメン取得 | 実装済み | `scripts/fetch_lineups_2026.py` | `output/today_lineups.csv` |
| セ・リーグ、パ・リーグの順位表生成 | 実装済み | `scripts/fetch_standings_2026.py` | `output/standings.csv` |

## Elo Calculation

| feature | status | main files | output |
| --- | --- | --- | --- |
| 全12球団のEloレーティング計算 | 実装済み | `scripts/elo.py`, `scripts/update_daily.py` | `output/elo_final_ranking.csv`, `output/elo_by_game.csv`, `output/elo_history.csv` |
| セ・リーグだけのElo出力 | 実装済み | `scripts/update_daily.py` | `output/central/` |
| パ・リーグだけのElo出力 | 実装済み | `scripts/update_daily.py` | `output/pacific/` |
| 交流戦期間のElo出力 | 実装済み | `scripts/update_daily.py` | `output/interleague/` |
| Elo推移表CSVの生成 | 実装済み | `scripts/make_elo_tables.py` | `output/elo_table.csv` |
| Elo推移グラフPNGの生成 | 実装済み | `scripts/make_elo_graphs.py` | `output/elo_graph.png`, `output/*/elo_graph.png` |
| K値、ロジスティック関数、初期値、ホーム補正の設定分離 | 実装済み | `scripts/elo_settings.py` | Elo計算、勝率予測 |

## Prediction

| feature | status | main files | output |
| --- | --- | --- | --- |
| 今日の対戦カードごとのElo勝率計算 | 実装済み | `scripts/update_today_probabilities.py` | `output/today_probabilities.csv` |
| 今日の対戦カードごとのElo変動シミュレーション | 実装済み | `scripts/update_today_probabilities.py`, `site_builder/schedule.py` | `output/today_probabilities.csv`, `site/index.html` |
| 今日の対戦カードごとの今季対戦成績表示 | 実装済み | `site_builder/schedule.py` | `site/index.html` |
| 予告先発とElo勝率の同時表示 | 実装済み | `scripts/update_today_probabilities.py`, `site_builder/schedule.py` | `site/index.html` |
| セ・リーグ、パ・リーグのタブ別試合予定表示 | 実装済み | `site_builder/schedule.py` | `site/index.html` |
| スタメン取得済みカードの表示 | 実装済み | `scripts/fetch_lineups_2026.py`, `site_builder/schedule.py` | `output/today_lineups.csv`, `site/index.html` |

## Site

| feature | status | main files | output |
| --- | --- | --- | --- |
| Eloダッシュボード生成 | 実装済み | `scripts/make_site.py`, `site_builder/dashboard.py` | `site/index.html` |
| 全体、セ・リーグ、パ・リーグ、交流戦タブ | 実装済み | `site_builder/payload.py`, `site_builder/dashboard.py` | `site/index.html` |
| Elo推移グラフ表示 | 実装済み | `scripts/make_elo_graphs.py`, `site_builder/dashboard.py` | `site/index.html` |
| Eloランキング表表示 | 実装済み | `site_builder/tables.py`, `site_builder/dashboard.py` | `site/index.html` |
| Elo推移表表示 | 実装済み | `site_builder/tables.py`, `site_builder/dashboard.py` | `site/index.html` |
| 今日の試合予定、勝率、予告先発表示 | 実装済み | `site_builder/schedule.py` | `site/index.html` |
| 順位表表示 | 実装済み | `site_builder/standings.py` | `site/index.html` |
| スタメン表示 | 実装済み | `site_builder/schedule.py` | `site/index.html` |
| 中止試合のスタメン欄を試合中止として表示 | 実装済み | `site_builder/schedule.py` | `site/index.html` |
| セ・リーグ、パ・リーグの球団別ページ | 実装済み | `site_builder/team_pages.py` | `site/central/`, `site/pacific/` |
| 球団ページの直近10試合表示 | 実装済み | `site_builder/team_pages.py` | 各球団ページ |
| 球団ページのElo勝率表示 | 実装済み | `site_builder/team_pages.py` | 各球団ページ |
| 球団カラーを使ったグラフ、カード、表の表示 | 実装済み | `site_builder/config.py`, `scripts/make_elo_graphs.py` | `site/index.html`, `output/*.png` |

## Automation

| feature | status | main files | output |
| --- | --- | --- | --- |
| GitHub Actionsによる日次自動更新 | 実装済み | `.github/workflows/npb-elo-daily.yml` | GitHub上のCSV、HTML、画像 |
| 朝の予定、勝率、予告先発更新 | 実装済み | `.github/workflows/npb-elo-daily.yml` | `output/today_probabilities.csv`, `site/` |
| 夜の試合結果、Elo、サイト更新 | 実装済み | `.github/workflows/npb-elo-daily.yml` | `game_results_jp_2026.csv`, `output/`, `site/` |
| 低遅延スタメン更新用ワークフロー | 実装済み | `.github/workflows/npb-elo-lineups.yml` | `output/today_lineups.csv`, `site/` |
| workflow_dispatchによる外部cron起動 | 実装済み | `.github/workflows/npb-elo-lineups.yml` | GitHub Actions実行 |
| GitHub Pages公開 | 実装済み | `index.html`, `site/` | `https://hrt2223.github.io/npb-elo/` |
| ローカルPCでの一括更新 | 実装済み | `tasks/daily_update.ps1` | ローカルのCSV、HTML、画像 |
| GitHub更新データのローカル同期 | 実装済み | `tasks/sync_from_github.ps1` | ローカルの生成データ |
| Windowsログオン時のローカル同期 | 実装済み | `tasks/install_startup_sync.ps1` | スタートアップ登録 |

## Documentation

| feature | status | file |
| --- | --- | --- |
| プロジェクト概要 | 実装済み | `docs/README.md` |
| フォルダ構成 | 実装済み | `docs/PROJECT_STRUCTURE.md` |
| 更新フローとPC同期の説明 | 実装済み | `docs/UPDATE_FLOW.md` |
| 実装済み機能一覧 | 実装済み | `docs/FEATURES.md` |
| ゼミ発表資料生成 | 実装済み | `scripts/create_seminar_ppt.py` |

## Update Rule

新しい機能を追加したら、該当するカテゴリの表に1行追加します。

追記する内容:

| item | description |
| --- | --- |
| `feature` | 何ができるようになったか |
| `status` | `実装済み`、`一部実装`、`検証中` のいずれか |
| `main files` | 主に関係するコード |
| `output` | 生成されるCSV、HTML、画像、または表示場所 |
