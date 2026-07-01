# AI Handoff Notes

このファイルは、別トークや別AIに `npb/2026` の作業を引き継ぐときに最初に読ませるためのメモです。
対象は `C:\2026\kenkyu\elo\npb\2026` です。

## 最初に守ること

- ユーザーの未コミット変更を勝手に戻さない。
- `npb/2025/` は今後GitHubへpushしない。`.gitignore` でも除外済み。
- 未追跡の `npb/2026/docs/それ.md` はユーザー側のメモとして扱い、明示されない限り触らない。
- 生成物を更新したら、必要に応じて `output/` と `site/` も再生成する。
- 試合結果や順位表は日々変わるため、最新性が必要な作業ではローカルCSVだけを信じ切らず、取得スクリプトやGitHub Actionsの実行状況も確認する。
- Git操作、push、外部サイト取得、pip install は権限やネットワークが必要になることがある。
- 予告先発は、当日分は月別日程ページの `先発：...` を優先し、足りない分を公式予告先発ページで補完する。公式予告先発ページは翌日分へ切り替わることがある。

## 現在のプロジェクト概要

`npb/2026` は、NPB 2026年シーズンの試合結果を取得し、Eloレーティング、今日の勝率予測、順位表、スタメン表示を作り、GitHub Pagesで公開するプロジェクト。

主な入口:

| path | role |
| --- | --- |
| `game_results_jp_2026.csv` | Elo計算の入力になる試合結果CSV |
| `scripts/fetch_results_2026.py` | NPB公式から試合結果を取得 |
| `scripts/update_daily.py` | 試合結果CSVからEloを再計算 |
| `scripts/update_today_probabilities.py` | 今日の予定、勝率、予告先発を作成 |
| `scripts/fetch_lineups_2026.py` | 試合開始前後のスタメンを取得 |
| `scripts/fetch_standings_2026.py` | 試合結果CSVから順位表を計算 |
| `scripts/make_site.py` | `site/` のHTML生成 |
| `site_builder/` | サイト生成ロジック |
| `.github/workflows/npb-elo-daily.yml` | 本番の日次更新 |
| `.github/workflows/npb-elo-lineups.yml` | 低遅延スタメン更新 |

詳しい構成は `docs/PROJECT_STRUCTURE.md`、更新フローは `docs/UPDATE_FLOW.md`、実装済み機能は `docs/FEATURES.md` を読む。

## 通常の更新フロー

作業ディレクトリは `npb/2026`。

```powershell
python scripts/fetch_results_2026.py --month <現在月> --merge-existing
python scripts/update_daily.py
python scripts/make_elo_tables.py
python scripts/make_elo_graphs.py
python scripts/update_today_probabilities.py
python scripts/fetch_lineups_2026.py --minutes-before 60
python scripts/fetch_standings_2026.py
python scripts/make_site.py
```

GitHub Actionsの日次更新も基本的にこの順番で動く。

## 重要なデータルール

### 試合結果CSV

- `game_results_jp_2026.csv` は1試合につき2行。ホーム側とビジター側の行を持つ。
- `GameID` は試合単位の識別子。
- 中止、未成立、ノーゲームはCSVに入れない。
- `fetch_results_2026.py --month <月> --merge-existing` は、対象月の既存行を削除してから公式ページで取得できた完了試合を入れ直す。
- これは、後から中止扱いになった試合がCSVに残り続ける事故を防ぐため。

### 順位表

- `output/standings.csv` はNPBの順位表ページを直接保存するのではなく、`game_results_jp_2026.csv` から勝敗・引分を集計して作る。
- 交流戦も公式戦として含める。
- 中止試合はCSVに入らないので、順位表にも含めない。
- 同率時の並びは `fetch_standings_2026.py` の実装に従う。公式順位とズレる場合は、勝率、勝利数、敗戦数、チーム順などのタイブレークを確認する。

### Elo

- Elo設定は `scripts/elo_settings.py` に集約されている。
- 設定変更後は、Elo CSV、グラフ、サイトを再生成する。
- 全体、セ・リーグ、パ・リーグ、交流戦の出力がある。

## 自動更新の考え方

本番はGitHub Actions。手元PCは確認用。

### 日次更新

`.github/workflows/npb-elo-daily.yml`

- 09:07 JST: 今日の予定、勝率、予告先発などを更新。
- 23:55 JST: 当日の結果を取り込み、Eloとサイトを更新。
- cronを00分ちょうどにしない。GitHub Actionsが混みやすいため、数分ずらす。

### 低遅延スタメン更新

`.github/workflows/npb-elo-lineups.yml`

- `workflow_dispatch` で外部から起動できる。
- cron-job.org などからGitHub REST APIへPOSTして起動する設計。
- Elo再計算やグラフ生成は省き、予定、スタメン、順位表、HTMLだけを更新する。
- フル更新と軽量更新は同じ concurrency グループにして、push競合を避ける。

## 過去に起きた問題と対策

### 6/28順位表が公式とズレた

原因:

- 6月のCSVに、公式ページでは中止扱いになっている11試合が残っていた。
- 以前の `--merge-existing` は既存月データを消さずにマージしていたため、後から中止になった行が残り続けた。

対策:

- 月次再取得時に対象月の既存行を削除してから完了試合だけ入れ直すよう修正済み。
- 月次パーサで開始時刻と勝敗情報を確認できる行だけ保存するよう強化済み。
- 修正後、6月の完了試合は111試合、累計は424試合になり、順位表が公式値と一致した。

関連コミット:

- `38df74d fix: replace stale monthly results before merge`
- `e601a5e fix: require result start times when parsing monthly games`

### docsの文字化け

- `docs/UPDATE_FLOW.md` はUTF-8で修正済み。
- `docs/FEATURES.md` は文字化けしていたため、日本語で作り直し済み。
- 文字化けチェックでは `縺`、`繝` などの断片が残っていないか確認する。

``

## 作業前チェック

別AIは作業開始時に必ず確認する。

```powershell
git status --short
git diff --name-only
```

未コミット変更がある場合:

- 自分が触るファイルと関係するか確認する。
- 関係ない変更は触らない。
- 同じファイルに変更がある場合は、差分を読んでから追記・修正する。

## よく使う確認コマンド

```powershell
# 実装ファイル一覧
rg --files .\npb\2026

# 文字化け断片チェック
rg -n "縺|繝|蜿|螳|譁|荳|讖|隕|謗|陦" .\npb\2026\docs

# 最新Eloサマリ
Get-Content .\npb\2026\output\elo_latest.txt -Encoding UTF8

# 順位表
Get-Content .\npb\2026\output\standings.csv -Encoding UTF8

# Python構文チェック
python -m py_compile .\npb\2026\scripts\fetch_results_2026.py
```

## コミット時の注意

- `npb/2025/` は追加しない。
- `npb/2026/docs/それ.md` は明示されない限り追加しない。
- 生成物を含めるかどうかは作業内容で判断する。
  - データ更新なら `game_results_jp_2026.csv`、`output/`、`site/` を含める。
  - コード修正だけなら、必要なスクリプトやdocsだけに絞る。
- コミット前に `git status --short` と `git diff --cached --stat` を確認する。

## ユーザーの意図

- 一番時間ラグが少ない形で、スタメンや当日情報をサイトに反映したい。
- GitHub Actionsを本番更新にし、cron-job.org の `workflow_dispatch` 起動で混雑を避けたい。
- 順位表はNPB順位表ページではなく、試合結果CSVから計算する方針。
- 中止、ノーゲーム、未成立試合がCSVや順位表に混ざらないことを重視している。
- 2025年データはローカル保持で、今後GitHubには上げたくない。
