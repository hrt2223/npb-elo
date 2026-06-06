from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

TARGETS = [
    (OUTPUT_DIR, "2026 NPB Elo Ratings"),
    (OUTPUT_DIR / "central", "2026 Central League Elo Ratings"),
    (OUTPUT_DIR / "pacific", "2026 Pacific League Elo Ratings"),
    (OUTPUT_DIR / "interleague", "2026 Interleague Elo Ratings"),
]

TEAM_COLORS = {
    "阪神": "#f7d417",
    "巨人": "#f47b20",
    "広島": "#d71920",
    "中日": "#003f7f",
    "DeNA": "#00a9e0",
    "ヤクルト": "#1f9d55",
}


def setup_font() -> None:
    plt.rcParams["font.family"] = [
        "Yu Gothic",
        "Meiryo",
        "MS Gothic",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False


def make_graph(target_dir: Path, title: str) -> Path:
    table_path = target_dir / "elo_table.csv"
    if not table_path.exists():
        raise FileNotFoundError(f"Missing table file: {table_path}")

    table_df = pd.read_csv(table_path, encoding="utf-8-sig")
    output_path = target_dir / "elo_graph.png"

    setup_font()
    fig, ax = plt.subplots(figsize=(12, 7))

    if table_df.empty or len(table_df.columns) <= 1:
        ax.text(0.5, 0.5, "No games found", ha="center", va="center", fontsize=16)
        ax.set_axis_off()
    else:
        table_df["date"] = pd.to_datetime(table_df["date"])
        latest_date = table_df["date"].max().strftime("%Y-%m-%d")
        for team in table_df.columns:
            if team == "date":
                continue
            ax.plot(
                table_df["date"],
                table_df[team],
                linewidth=2,
                label=team,
                color=TEAM_COLORS.get(team),
            )

        ax.set_title(title)
        ax.text(
            0.0,
            1.01,
            f"Latest date: {latest_date}",
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=10,
        )
        ax.set_xlabel("Date")
        ax.set_ylabel("Elo")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5))
        fig.autofmt_xdate()

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return output_path


def main() -> None:
    for target_dir, title in TARGETS:
        output_path = make_graph(target_dir, title)
        print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
