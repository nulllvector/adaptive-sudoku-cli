from __future__ import annotations

from sudoku.board import Board


def solve(board: Board) -> Board | None:
    if not board.is_valid_state():
        return None

    return _solve_recursive(board)


def has_unique_solution(board: Board) -> bool:
    """Return whether a board has exactly one solution."""
    return count_solutions(board, limit=2) == 1


def count_solutions(board: Board, limit: int = 2) -> int:
    if limit < 1:
        raise ValueError("limit must be at least 1.")
    if not board.is_valid_state():
        return 0

    return _count_recursive(board, limit)


def _solve_recursive(board: Board) -> Board | None:
    next_cell = _best_empty_cell(board)
    if next_cell is None:
        return board if board.is_valid_state() else None

    row, col, candidates = next_cell
    for value in candidates:
        solved = _solve_recursive(board.place(row, col, value))
        if solved is not None:
            return solved

    return None


def _count_recursive(board: Board, limit: int) -> int:
    next_cell = _best_empty_cell(board)
    if next_cell is None:
        return 1

    row, col, candidates = next_cell
    total = 0
    for value in candidates:
        total += _count_recursive(board.place(row, col, value), limit - total)
        if total >= limit:
            return total

    return total


def _best_empty_cell(board: Board) -> tuple[int, int, tuple[int, ...]] | None:
    best: tuple[int, int, tuple[int, ...]] | None = None

    for row in range(9):
        for col in range(9):
            if not board.is_empty(row, col):
                continue

            candidates = _candidates(board, row, col)
            if not candidates:
                return row, col, ()
            if best is None or len(candidates) < len(best[2]):
                best = row, col, candidates

    return best


def _candidates(board: Board, row: int, col: int) -> tuple[int, ...]:
    return tuple(value for value in range(1, 10) if board.is_valid_move(row, col, value))
