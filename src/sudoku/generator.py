from __future__ import annotations

import random

from sudoku.board import Board
from sudoku.difficulty import Difficulty, GIVEN_RANGES
from sudoku.puzzle import Puzzle
from sudoku.solver import has_unique_solution


def generate_puzzle(difficulty: Difficulty, rng: random.Random | None = None) -> Puzzle:
    """Generate a puzzle for the requested difficulty."""
    rng = rng or random.Random()
    solution = generate_solved_board(rng)
    target_givens = rng.choice(tuple(GIVEN_RANGES[difficulty]))

    puzzle_grid = [list(row) for row in solution.grid]
    cells = [(row, col) for row in range(9) for col in range(9)]
    rng.shuffle(cells)

    for row, col in cells:
        if _given_count(puzzle_grid) <= target_givens:
            break

        removed_value = puzzle_grid[row][col]
        puzzle_grid[row][col] = 0
        candidate = Board.from_rows(puzzle_grid)

        if not has_unique_solution(candidate):
            puzzle_grid[row][col] = removed_value

    return Puzzle(
        starting_board=Board.from_rows(puzzle_grid),
        solution=solution,
        difficulty=difficulty,
    )


def generate_solved_board(rng: random.Random | None = None) -> Board:
    rng = rng or random.Random()
    solved = _fill_board(Board.empty(), rng)
    if solved is None:
        raise RuntimeError("Could not generate a solved Sudoku board.")
    return solved


def _fill_board(board: Board, rng: random.Random) -> Board | None:
    empty_cell = _first_empty_cell(board)
    if empty_cell is None:
        return board

    row, col = empty_cell
    values = list(range(1, 10))
    rng.shuffle(values)

    for value in values:
        if board.is_valid_move(row, col, value):
            solved = _fill_board(board.place(row, col, value), rng)
            if solved is not None:
                return solved

    return None


def _first_empty_cell(board: Board) -> tuple[int, int] | None:
    for row in range(9):
        for col in range(9):
            if board.is_empty(row, col):
                return row, col
    return None


def _given_count(grid: list[list[int]]) -> int:
    return sum(1 for row in grid for value in row if value != 0)
