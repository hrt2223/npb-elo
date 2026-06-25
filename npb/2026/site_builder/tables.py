from __future__ import annotations

import html
from pathlib import Path

import pandas as pd


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig")

def format_number(value) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)

def df_to_table(df: pd.DataFrame, *, max_rows: int | None = None) -> str:
    if df.empty:
        return '<div class="empty">データがありません</div>'

    if max_rows is not None:
        df = df.tail(max_rows)

    header = "".join(f"<th>{html.escape(str(col))}</th>" for col in df.columns)
    rows = []
    for _, row in df.iterrows():
        cells = "".join(f"<td>{html.escape(format_number(row[col]))}</td>" for col in df.columns)
        rows.append(f"<tr>{cells}</tr>")

    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"

def read_latest_text(path: Path) -> dict[str, str]:
    if not path.exists():
        return {"updated": "-", "period": "-", "games": "-"}

    values = {"updated": "-", "period": "-", "games": "-"}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Updated at:"):
            values["updated"] = line.replace("Updated at:", "").strip()
        elif line.startswith("Period:"):
            values["period"] = line.replace("Period:", "").strip()
        elif line.startswith("Games:"):
            values["games"] = line.replace("Games:", "").strip()
    return values
