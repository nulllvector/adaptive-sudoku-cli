from __future__ import annotations

from dataclasses import dataclass

from sudoku.board import Board, BoardError
from sudoku.puzzle import Puzzle


@dataclass(frozen=True)
class GameSession:
    puzzle: Puzzle
    board: Board
    mistakes: int = 0
    hints_used: int = 0
    invalid_attempts: int = 0

    @classmethod
    def start(cls, puzzle: Puzzle) -> "GameSession":
        return cls(puzzle=puzzle, board=puzzle.starting_board)

    def make_move(self, row: int, col: int, value: int) -> "GameSession":
        if self.puzzle.is_given(row, col):
            raise BoardError("Cannot change a given cell.")

        expected = self.puzzle.solution.value_at(row, col)
        if value != expected:
            return GameSession(
                puzzle=self.puzzle,
                board=self.board,
                mistakes=self.mistakes + 1,
                hints_used=self.hints_used,
                invalid_attempts=self.invalid_attempts,
            )

        return GameSession(
            puzzle=self.puzzle,
            board=self.board.place(row, col, value),
            mistakes=self.mistakes,
            hints_used=self.hints_used,
            invalid_attempts=self.invalid_attempts,
        )

    def use_hint(self) -> "GameSession":
        for row in range(9):
            for col in range(9):
                if self.board.is_empty(row, col):
                    value = self.puzzle.solution.value_at(row, col)
                    return GameSession(
                        puzzle=self.puzzle,
                        board=self.board.place(row, col, value),
                        mistakes=self.mistakes,
                        hints_used=self.hints_used + 1,
                        invalid_attempts=self.invalid_attempts,
                    )
        return self

    def record_invalid_attempt(self) -> "GameSession":
        return GameSession(
            puzzle=self.puzzle,
            board=self.board,
            mistakes=self.mistakes,
            hints_used=self.hints_used,
            invalid_attempts=self.invalid_attempts + 1,
        )

    def is_won(self) -> bool:
        return self.board == self.puzzle.solution
