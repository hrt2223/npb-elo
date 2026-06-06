import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# =========================
# 設定
# =========================

CSV_PATH = "game_results_jp_2025.csv"

INITIAL_ELO = 1500
K = 20
HOME_ADVANTAGE = 35

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


CENTRAL_TEAMS = {
    "阪神タイガース": "阪神",
    "横浜DeNAベイスターズ": "DeNA",
    "読売ジャイアンツ": "巨人",
    "中日ドラゴンズ": "中日",
    "広島東洋カープ": "広島",
    "東京ヤクルトスワローズ": "ヤクルト",
}


# =========================
# CSV読み込み
# =========================

def load_csv():
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df["日付"] = pd.to_datetime(df["日付"])

    # レギュラーシーズンだけ使う
    df = df[df["ゲームタイプ"] == "公式戦"].copy()

    return df


# =========================
# 1試合1行に変換
# =========================

def make_game_table(df):
    games = []

    for game_id, group in df.groupby("GameID"):
        if len(group) != 2:
            continue

        home_rows = group[group["ホーム・ビジター"] == "ホーム"]
        away_rows = group[group["ホーム・ビジター"] == "ビジター"]

        if len(home_rows) != 1 or len(away_rows) != 1:
            continue

        home = home_rows.iloc[0]
        away = away_rows.iloc[0]

        home_team = home["球団"]
        away_team = away["球団"]

        # セ・リーグ6球団同士の試合だけ使う
        if home_team not in CENTRAL_TEAMS or away_team not in CENTRAL_TEAMS:
            continue

        games.append({
            "date": home["日付"],
            "game_id": game_id,
            "home": CENTRAL_TEAMS[home_team],
            "away": CENTRAL_TEAMS[away_team],
            "home_score": int(home["スコア"]),
            "away_score": int(away["スコア"]),
            "stadium": home["球場"],
            "start_time": home["試合開始"],
        })

    game_df = pd.DataFrame(games)

    if game_df.empty:
        raise RuntimeError("セ・リーグ公式戦のデータが見つかりませんでした。")

    game_df = game_df.sort_values(
        ["date", "start_time", "game_id"]
    ).reset_index(drop=True)

    return game_df


# =========================
# Elo計算
# =========================

def expected_score(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def result_from_score(home_score, away_score):
    if home_score > away_score:
        return 1.0
    elif home_score < away_score:
        return 0.0
    else:
        return 0.5


def update_elo(home_rating, away_rating, home_score, away_score):
    actual_home = result_from_score(home_score, away_score)

    expected_home = expected_score(
        home_rating + HOME_ADVANTAGE,
        away_rating
    )

    change = K * (actual_home - expected_home)

    new_home_rating = home_rating + change
    new_away_rating = away_rating - change

    return new_home_rating, new_away_rating, expected_home, change


def calculate_elo(game_df):
    teams = ["阪神", "DeNA", "巨人", "中日", "広島", "ヤクルト"]
    ratings = {team: INITIAL_ELO for team in teams}

    game_records = []
    history_records = []

    first_date = game_df["date"].min()

    for team in teams:
        history_records.append({
            "date": first_date - pd.Timedelta(days=1),
            "team": team,
            "elo": INITIAL_ELO
        })

    for _, row in game_df.iterrows():
        date = row["date"]
        home = row["home"]
        away = row["away"]
        home_score = row["home_score"]
        away_score = row["away_score"]

        old_home = ratings[home]
        old_away = ratings[away]

        new_home, new_away, expected_home, change = update_elo(
            old_home,
            old_away,
            home_score,
            away_score
        )

        ratings[home] = new_home
        ratings[away] = new_away

        game_records.append({
            "date": date,
            "game_id": row["game_id"],
            "home": home,
            "away": away,
            "home_score": home_score,
            "away_score": away_score,
            "stadium": row["stadium"],
            "start_time": row["start_time"],
            "home_elo_before": old_home,
            "away_elo_before": old_away,
            "home_expected_win_rate": expected_home,
            "home_elo_change": change,
            "home_elo_after": new_home,
            "away_elo_after": new_away,
        })

        for team in teams:
            history_records.append({
                "date": date,
                "team": team,
                "elo": ratings[team]
            })

    game_elo_df = pd.DataFrame(game_records)
    history_df = pd.DataFrame(history_records)

    ranking_df = (
        pd.DataFrame({
            "team": list(ratings.keys()),
            "final_elo": list(ratings.values())
        })
        .sort_values("final_elo", ascending=False)
        .reset_index(drop=True)
    )

    ranking_df["rank"] = ranking_df.index + 1

    return ranking_df, game_elo_df, history_df


# =========================
# グラフ
# =========================

def setup_japanese_font():
    plt.rcParams["font.family"] = [
        "Yu Gothic",
        "Meiryo",
        "MS Gothic",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False


def plot_elo(history_df):
    setup_japanese_font()

    plt.figure(figsize=(12, 6))

    for team in history_df["team"].unique():
        tmp = history_df[history_df["team"] == team]
        plt.plot(tmp["date"], tmp["elo"], label=team)

    plt.title("2025年 セ・リーグ Eloレーティング推移")
    plt.xlabel("日付")
    plt.ylabel("Eloレーティング")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    output_path = OUTPUT_DIR / "central_2025_elo_graph.png"
    plt.savefig(output_path, dpi=300)
    plt.show()

    print(f"グラフを保存しました: {output_path}")


# =========================
# 実行
# =========================

def main():
    raw_df = load_csv()
    game_df = make_game_table(raw_df)

    print("==============================")
    print("読み込んだデータ")
    print("==============================")
    print(f"セ・リーグ公式戦の試合数: {len(game_df)}")
    print(f"期間: {game_df['date'].min().date()} ～ {game_df['date'].max().date()}")
    print(f"引き分け数: {(game_df['home_score'] == game_df['away_score']).sum()}")

    print("\n各球団の試合数")
    team_counts = pd.concat([game_df["home"], game_df["away"]]).value_counts()
    print(team_counts)

    games_path = OUTPUT_DIR / "central_2025_games.csv"
    game_df.to_csv(games_path, index=False, encoding="utf-8-sig")

    ranking_df, game_elo_df, history_df = calculate_elo(game_df)

    game_elo_path = OUTPUT_DIR / "central_2025_elo_by_game.csv"
    history_path = OUTPUT_DIR / "central_2025_elo_history.csv"
    ranking_path = OUTPUT_DIR / "central_2025_elo_final_ranking.csv"

    game_elo_df.to_csv(game_elo_path, index=False, encoding="utf-8-sig")
    history_df.to_csv(history_path, index=False, encoding="utf-8-sig")
    ranking_df.to_csv(ranking_path, index=False, encoding="utf-8-sig")

    print("\n==============================")
    print("2025年 セ・リーグ Elo最終ランキング")
    print("==============================")
    print(ranking_df[["rank", "team", "final_elo"]])

    print("\n==============================")
    print("保存ファイル")
    print("==============================")
    print(games_path)
    print(game_elo_path)
    print(history_path)
    print(ranking_path)

    plot_elo(history_df)


if __name__ == "__main__":
    main()