from __future__ import annotations

from dataclasses import dataclass

from sudoku.board import Board
from sudoku.difficulty import Difficulty


@dataclass(frozen=True)
class Puzzle:
    starting_board: Board
    solution: Board
    difficulty: Difficulty

    @property
    def given_count(self) -> int:
        return sum(
            1
            for row in range(9)
            for col in range(9)
            if not self.starting_board.is_empty(row, col)
        )

    def is_given(self, row: int, col: int) -> bool:
        return not self.starting_board.is_empty(row, col)
