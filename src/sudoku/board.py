from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


Grid = tuple[tuple[int, ...], ...]


class BoardError(ValueError):
    """Raised when a board or move is invalid."""


@dataclass(frozen=True)
class Board:
    grid: Grid

    @classmethod
    def empty(cls) -> "Board":
        return cls.from_rows([[0 for _ in range(9)] for _ in range(9)])

    @classmethod
    def from_rows(cls, rows: Iterable[Iterable[int]]) -> "Board":
        grid = tuple(tuple(row) for row in rows)
        if len(grid) != 9 or any(len(row) != 9 for row in grid):
            raise BoardError("A Sudoku board must be a 9x9 grid.")

        for row in grid:
            for value in row:
                if value < 0 or value > 9:
                    raise BoardError("Board values must be between 0 and 9.")

        return cls(grid)

    def value_at(self, row: int, col: int) -> int:
        self._check_position(row, col)
        return self.grid[row][col]

    def is_empty(self, row: int, col: int) -> bool:
        return self.value_at(row, col) == 0

    def row_values(self, row: int) -> tuple[int, ...]:
        self._check_index(row, "row")
        return self.grid[row]

    def column_values(self, col: int) -> tuple[int, ...]:
        self._check_index(col, "column")
        return tuple(row[col] for row in self.grid)

    def box_values(self, row: int, col: int) -> tuple[int, ...]:
        self._check_position(row, col)
        start_row = (row // 3) * 3
        start_col = (col // 3) * 3
        return tuple(
            self.grid[r][c]
            for r in range(start_row, start_row + 3)
            for c in range(start_col, start_col + 3)
        )

    def is_valid_move(self, row: int, col: int, value: int) -> bool:
        self._check_position(row, col)
        self._check_move_value(value)

        if not self.is_empty(row, col):
            return False

        return (
            value not in self.row_values(row)
            and value not in self.column_values(col)
            and value not in self.box_values(row, col)
        )

    def place(self, row: int, col: int, value: int) -> "Board":
        if not self.is_valid_move(row, col, value):
            raise BoardError("Move violates Sudoku rules.")

        new_grid = [list(row_values) for row_values in self.grid]
        new_grid[row][col] = value
        return Board.from_rows(new_grid)

    def is_complete(self) -> bool:
        return all(value != 0 for row in self.grid for value in row)

    def is_valid_state(self) -> bool:
        groups = []
        groups.extend(self.row_values(row) for row in range(9))
        groups.extend(self.column_values(col) for col in range(9))
        groups.extend(self.box_values(row, col) for row in range(0, 9, 3) for col in range(0, 9, 3))
        return all(_has_no_duplicates(group) for group in groups)

    @staticmethod
    def _check_index(index: int, label: str) -> None:
        if index < 0 or index > 8:
            raise BoardError(f"{label} index must be between 0 and 8.")

    @classmethod
    def _check_position(cls, row: int, col: int) -> None:
        cls._check_index(row, "row")
        cls._check_index(col, "column")

    @staticmethod
    def _check_move_value(value: int) -> None:
        if value < 1 or value > 9:
            raise BoardError("Move value must be between 1 and 9.")


def _has_no_duplicates(values: Iterable[int]) -> bool:
    seen: set[int] = set()
    for value in values:
        if value == 0:
            continue
        if value in seen:
            return False
        seen.add(value)
    return True
