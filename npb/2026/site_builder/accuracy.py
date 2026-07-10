from __future__ import annotations

import html
from pathlib import Path

import pandas as pd


BIN_LABELS = ["〜39%", "40〜49%", "50〜59%", "60%〜"]


def prediction_accuracy_html(by_game_path: Path) -> str:
    """Build a calibration summary from each game's pre-game Elo prediction."""
    if not by_game_path.exists():
        return '<div class="empty">予測精度を算出する試合データがありません</div>'

    df = pd.read_csv(by_game_path, encoding="utf-8-sig")
    required = {"home_expected_win_rate", "home_score", "away_score"}
    if df.empty or not required.issubset(df.columns):
        return '<div class="empty">予測精度を算出する試合データがありません</div>'

    df = df.dropna(subset=list(required)).copy()
    df["predicted"] = pd.to_numeric(df["home_expected_win_rate"], errors="coerce")
    df["actual"] = (df["home_score"] > df["away_score"]).astype(float)
    df.loc[df["home_score"] == df["away_score"], "actual"] = 0.5
    df = df.dropna(subset=["predicted"])
    if df.empty:
        return '<div class="empty">予測精度を算出する試合データがありません</div>'

    decisive = df[df["actual"] != 0.5]
    hit_rate = ((decisive["predicted"] >= 0.5) == (decisive["actual"] == 1.0)).mean() * 100 if not decisive.empty else 0.0
    brier = ((df["predicted"] - df["actual"]) ** 2).mean()

    bins = [-0.001, 0.4, 0.5, 0.6, 1.001]
    df["band"] = pd.cut(df["predicted"], bins=bins, labels=BIN_LABELS, right=False)
    rows = []
    for label in BIN_LABELS:
        group = df[df["band"] == label]
        if group.empty:
            rows.append(f"<tr><td>{label}</td><td>—</td><td>—</td><td>—</td></tr>")
            continue
        predicted = group["predicted"].mean() * 100
        actual = group["actual"].mean() * 100
        delta = actual - predicted
        delta_text = f"+{delta:.1f}pt" if delta >= 0 else f"{delta:.1f}pt"
        rows.append(
            f'<tr><td>{label}</td><td>{len(group)}</td><td>{predicted:.1f}%</td>'
            f'<td>{actual:.1f}% <span class="calibration-delta">({delta_text})</span></td></tr>'
        )

    draw_note = "（引き分けは0.5勝としてBrier scoreに算入）" if (df["actual"] == 0.5).any() else ""
    return f'''<div class="accuracy-body">
      <div class="accuracy-metrics">
        <div><span>予測対象試合</span><strong>{len(df)}</strong></div>
        <div><span>的中率</span><strong>{hit_rate:.1f}%</strong><small>引き分け除く</small></div>
        <div><span>Brier score</span><strong>{brier:.3f}</strong><small>小さいほど良い</small></div>
      </div>
      <div class="accuracy-caption">ホーム勝率の予測値と実際のホーム勝率を比較 {html.escape(draw_note)}</div>
      <div class="table-wrap accuracy-table"><table>
        <thead><tr><th>予測ホーム勝率</th><th>試合数</th><th>予測平均</th><th>実績ホーム勝率</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table></div>
    </div>'''
