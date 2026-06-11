# Project Structure

このリポジトリは、NPB 2026シーズンの試合結果を取得し、Eloレーティング、今日の勝率予測、順位表を作って、GitHub Pagesで公開する構成です。

## Root

| path | role |
| --- | --- |
| `README.md` | プロジェクト概要と主要コマンド |
| `PROJECT_STRUCTURE.md` | このファイル。どこに何があるかの説明 |
| `index.html` | GitHub Pagesの入口。`npb/2026/site/index.html` へ案内する |
| `.nojekyll` | GitHub PagesでJekyll処理を無効にする設定 |
| `.gitignore` | Pythonキャッシュやローカルログなど、Git管理しないもの |
| `.github/workflows/npb-elo-daily.yml` | GitHub Actionsの自動更新設定 |
| `.vscode/launch.json` | VS Code用のローカル実行設定 |

## Production: `npb/2026`

2026年版の本番コードです。基本的に作業はこのフォルダで行います。

| path | role |
| --- | --- |
| `npb/2026/requirements.txt` | Python依存ライブラリ |
| `npb/2026/game_results_jp_2026.csv` | 2026年の試合結果CSV。Elo計算の入力 |
| `npb/2026/fetch_results_2026.py` | NPB公式サイトから一軍公式戦の試合結果を取得する |
| `npb/2026/elo.py` | Eloレーティング計算の中核ロジック |
| `npb/2026/update_daily.py` | 試合結果CSVからElo出力を作るメイン処理 |
| `npb/2026/make_elo_tables.py` | Elo推移表CSVを作る |
| `npb/2026/make_elo_graphs.py` | Elo推移グラフPNGを作る |
| `npb/2026/update_today_probabilities.py` | 今日の試合予定と勝率予測CSVを作る |
| `npb/2026/fetch_standings_2026.py` | 順位表CSVを作る |
| `npb/2026/make_site.py` | 静的サイトHTMLを生成する |
| `npb/2026/daily_update.ps1` | ローカルPCでまとめて更新するPowerShellスクリプト |
| `npb/2026/install_daily_task.ps1` | Windowsタスクスケジューラへ登録するための補助スクリプト |

## Generated Data: `npb/2026/output`

サイトと分析に使う生成済みデータです。GitHub Actionsが毎日更新します。

| path | role |
| --- | --- |
| `npb/2026/output/games.csv` | Elo計算に使った試合一覧 |
| `npb/2026/output/elo_by_game.csv` | 試合ごとのElo変化 |
| `npb/2026/output/elo_history.csv` | 日付ごとのElo履歴 |
| `npb/2026/output/elo_table.csv` | サイトの表で使うElo推移表 |
| `npb/2026/output/elo_final_ranking.csv` | 最新Eloランキング |
| `npb/2026/output/elo_latest.txt` | 最新日付、試合数などのサマリ |
| `npb/2026/output/elo_graph.png` | 全体のElo推移グラフ |
| `npb/2026/output/today_probabilities.csv` | 今日の試合予定と勝率予測 |
| `npb/2026/output/standings.csv` | セ・リーグ、パ・リーグの順位表 |
| `npb/2026/output/central/` | セ・リーグだけのElo出力 |
| `npb/2026/output/pacific/` | パ・リーグだけのElo出力 |
| `npb/2026/output/interleague/` | 交流戦期間のElo出力 |

## Site: `npb/2026/site`

GitHub Pagesで表示される静的サイトです。

| path | role |
| --- | --- |
| `npb/2026/site/index.html` | トップページ。グラフ、表、今日の試合、順位表を表示 |
| `npb/2026/site/central/` | セ・リーグ各球団ページ |
| `npb/2026/site/pacific/` | パ・リーグ各球団ページ |

球団ページでは、直近10試合の勝敗、相手、Elo変化を確認できます。

## Automation

| path | role |
| --- | --- |
| `.github/workflows/npb-elo-daily.yml` | GitHub上で毎日自動更新する本番用の設定 |
| `npb/2026/daily_update.ps1` | 手元のPCで同じ処理を動かすためのローカル用スクリプト |
| `npb/2026/install_daily_task.ps1` | 手元のPCで定期実行したい場合だけ使う |

PCを開かない日でも更新したい場合は、GitHub Actionsを使います。ローカルPCのタスクスケジューラは、PCが起動している時だけ動きます。

## Archive: `npb/2025`

2025年データと過去の検証コードです。2026年サイトの本番更新には使っていません。

| path | role |
| --- | --- |
| `npb/2025/game_results_jp_2025.csv` | 2025年の試合結果CSV |
| `npb/2025/a.py` | 2025年用の旧コード |
| `npb/2025/output/` | 2025年の旧出力 |

## Ignored Local Files

以下は実行すると作られますが、Git管理しません。

| path | reason |
| --- | --- |
| `npb/2026/__pycache__/` | Pythonの実行キャッシュ |
| `npb/2026/logs/` | ローカル実行時のログ |
| `.agents/`, `.codex/` | ローカル作業用の状態ファイル |

## Update Flow

通常の更新順です。

1. `fetch_results_2026.py` で試合結果を取得する
2. `update_daily.py` でEloを計算する
3. `make_elo_tables.py` で推移表を作る
4. `make_elo_graphs.py` でグラフを作る
5. `update_today_probabilities.py` で今日の試合予定と勝率を作る
6. `fetch_standings_2026.py` で順位表を作る
7. `make_site.py` でサイトを作る
