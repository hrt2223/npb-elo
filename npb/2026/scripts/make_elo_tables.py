from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

TARGETS = [
    OUTPUT_DIR,
    OUTPUT_DIR / "central",
    OUTPUT_DIR / "pacific",
    OUTPUT_DIR / "interleague",
]


def make_table(target_dir: Path) -> Path:
    history_path = target_dir / "elo_history.csv"
    if not history_path.exists():
        raise FileNotFoundError(f"Missing history file: {history_path}")

    history_df = pd.read_csv(history_path, encoding="utf-8-sig")
    if history_df.empty:
        table_df = pd.DataFrame(columns=["date"])
    else:
        history_df["date"] = pd.to_datetime(history_df["date"]).dt.strftime("%Y-%m-%d")
        table_df = (
            history_df.pivot_table(
                index="date",
                columns="team",
                values="elo",
                aggfunc="last",
            )
            .sort_index()
            .round(1)
            .reset_index()
        )
        table_df.columns.name = None

    output_path = target_dir / "elo_table.csv"
    table_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


def main() -> None:
    for target_dir in TARGETS:
        output_path = make_table(target_dir)
        print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
