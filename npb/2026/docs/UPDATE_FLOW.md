# Update Flow

このプロジェクトの更新は、GitHub Actionsを本番、手元PCを確認用として扱います。

## 本番更新

本番更新は `.github/workflows/npb-elo-daily.yml` が実行します。

1. `fetch_results_2026.py`
   - NPB公式から試合結果を取得する
   - `game_results_jp_2026.csv` を更新する
2. `update_daily.py`
   - `game_results_jp_2026.csv` からEloを再計算する
   - `output/elo_*` を更新する
3. `make_elo_tables.py`
   - Elo推移表を作る
4. `make_elo_graphs.py`
   - Elo推移グラフを作る
5. `update_today_probabilities.py`
   - 今日の試合予定を取得する
   - Eloから勝率を計算する
   - NPB公式の予告先発ページから予告先発を取得する
   - `output/today_probabilities.csv` を更新する
6. `fetch_lineups_2026.py`
   - 試合開始60分前以降のタイミングでスタメンを取得する
   - `output/today_lineups.csv` を更新する
7. `fetch_standings_2026.py`
   - 順位表を取得する
   - `output/standings.csv` を更新する
8. `make_site.py`
   - `site/index.html` と球団ページを作る

最後にGitHub Actionsが `game_results_jp_2026.csv`、`output/`、`site/` をコミットしてGitHubへpushします。GitHub Pagesはその内容を公開します。

## 低遅延のスタメン更新

スタメン反映は `.github/workflows/npb-elo-lineups.yml` でも実行できます。
このワークフローはElo再計算やグラフ生成を省き、次の処理だけを行います。

1. `update_today_probabilities.py`
2. `fetch_lineups_2026.py --minutes-before 60`
3. `fetch_standings_2026.py`
4. `make_site.py`
5. `output/today_probabilities.csv`、`output/today_lineups.csv`、`output/standings.csv`、`site/` をcommit & push

cron-job.org などの外部cronから GitHub REST API の `workflow_dispatch` をPOSTすると、GitHub Actionsのschedule混雑を避けて起動できます。

```text
POST https://api.github.com/repos/hrt2223/npb-elo/actions/workflows/npb-elo-lineups.yml/dispatches
```

Body:

```json
{"ref":"main"}
```

必要なヘッダー:

```text
Accept: application/vnd.github+json
Authorization: Bearer <GitHub fine-grained PAT>
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json
```

GitHub token は `hrt2223/npb-elo` だけに限定し、Actions の read/write 権限だけを付けます。
フル更新と軽量更新は同じ concurrency グループに入れているため、同時刻に起動してもpush競合を避けます。

## 予告先発の位置づけ

予告先発は試合結果CSVには入れません。理由は、Elo計算に直接使うデータではなく、今日の試合カード表示に使う当日情報だからです。

保存先は `output/today_probabilities.csv` です。

主な列:

| column | role |
| --- | --- |
| `home` | ホーム球団 |
| `away` | ビジター球団 |
| `home_probable_starter` | ホーム側の予告先発 |
| `away_probable_starter` | ビジター側の予告先発 |
| `home_win_probability` | ホーム側のElo勝率 |
| `away_win_probability` | ビジター側のElo勝率 |

サイトでは `make_site.py` がこのCSVを読み、今日の対戦予定カードに予告先発と勝率を表示します。

## 手元PCへの反映

GitHub Actionsはクラウド上で動くので、PCの電源がオフでもGitHub上のデータとサイトは更新されます。

ただし、PC内の `C:\2026\kenkyu\elo` は自動では変わりません。PC側へ反映するには、GitHubから同期する必要があります。

手動同期:

```powershell
cd C:\2026\kenkyu\elo\npb\2026
powershell -ExecutionPolicy Bypass -File .\sync_from_github.ps1
```

自動同期を登録:

```powershell
cd C:\2026\kenkyu\elo\npb\2026
powershell -ExecutionPolicy Bypass -File .\install_sync_task.ps1
```

登録できる環境では、このPCが使える時に以下のタイミングで `sync_from_github.ps1` が動きます。

| timing | purpose |
| --- | --- |
| ログオン時 | PCを開いた時に最新データへ寄せる |
| 09:15 | 朝のGitHub Actions更新後に反映する |
| 00:10 | 夜の試合結果更新後に反映する |

タスクスケジューラ登録で `Access is denied.` が出る場合は、スタートアップ方式を使います。

```powershell
cd C:\2026\kenkyu\elo\npb\2026
powershell -ExecutionPolicy Bypass -File .\install_startup_sync.ps1
```

この方式では、Windowsにログオンした時だけ `sync_from_github.ps1` が動きます。

`sync_from_github.ps1` は生成データだけを更新します。

対象:

| path | reason |
| --- | --- |
| `npb/2026/game_results_jp_2026.csv` | 最新の試合結果 |
| `npb/2026/output/` | Elo、勝率、予告先発、順位表、スタメンCSV |
| `npb/2026/site/` | GitHub Pagesで公開しているHTML |

コード作業中のファイルを壊さないため、Pythonコードや設定ファイルは同期対象にしていません。

## ローカルで全部更新する場合

PCが起動していて、手元でも取得からサイト生成まで実行したい場合は `daily_update.ps1` を使います。

```powershell
cd C:\2026\kenkyu\elo\npb\2026
powershell -ExecutionPolicy Bypass -File .\daily_update.ps1
```

このスクリプトも、試合結果取得後に `update_today_probabilities.py` を実行するため、今日の予定、勝率、予告先発を同じ更新フローで作ります。
