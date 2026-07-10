from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from fetch_results_2026 import ResultGame, ensure_month_replacement_is_safe


def game(day: int) -> ResultGame:
    return ResultGame(
        date=f"2026-07-{day:02d}",
        home="阪神",
        away="巨人",
        home_score=3,
        away_score=2,
        stadium="甲子園",
        start_time="18:00",
        game_id=f"NPB202607{day:02d}HTYG01",
    )


def rows_for(game_item: ResultGame) -> list[dict[str, str]]:
    return [
        {"日付": game_item.date, "球団": game_item.home, "ホーム・ビジター": "ホーム", "GameID": game_item.game_id},
        {"日付": game_item.date, "球団": game_item.away, "ホーム・ビジター": "ビジター", "GameID": game_item.game_id},
    ]


class MonthlyReplacementSafetyTests(unittest.TestCase):
    def test_rejects_partial_month_replacement(self) -> None:
        existing_rows = rows_for(game(1)) + rows_for(game(2))

        with self.assertRaisesRegex(RuntimeError, "Existing results were kept"):
            ensure_month_replacement_is_safe(existing_rows, [game(1)], year=2026, months=[7])

    def test_allows_same_or_larger_month_replacement(self) -> None:
        existing_rows = rows_for(game(1))
        ensure_month_replacement_is_safe(existing_rows, [game(1), game(2)], year=2026, months=[7])


if __name__ == "__main__":
    unittest.main()
