from sudoku.board import Board
from sudoku.solver import count_solutions, has_unique_solution, solve


PUZZLE_ROWS = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

SOLUTION_ROWS = [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9],
]


def test_solver_solves_known_puzzle():
    puzzle = Board.from_rows(PUZZLE_ROWS)

    assert solve(puzzle) == Board.from_rows(SOLUTION_ROWS)


def test_solver_returns_already_complete_valid_board():
    solution = Board.from_rows(SOLUTION_ROWS)

    assert solve(solution) == solution


def test_solver_returns_none_for_invalid_or_unsolvable_board():
    invalid_rows = [row[:] for row in PUZZLE_ROWS]
    invalid_rows[0][2] = 5

    assert solve(Board.from_rows(invalid_rows)) is None


def test_solution_count_stops_at_limit():
    empty = Board.empty()

    assert count_solutions(empty, limit=2) == 2


def test_unique_solution_detection():
    puzzle = Board.from_rows(PUZZLE_ROWS)
    empty = Board.empty()

    assert has_unique_solution(puzzle)
    assert not has_unique_solution(empty)
