import pytest

from sudoku.board import Board, BoardError


STARTING_ROWS = [
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


def test_board_requires_nine_rows_and_columns():
    with pytest.raises(BoardError):
        Board.from_rows([[0] * 9 for _ in range(8)])

    with pytest.raises(BoardError):
        Board.from_rows([[0] * 8 for _ in range(9)])


def test_board_rejects_values_outside_sudoku_range():
    rows = [[0] * 9 for _ in range(9)]
    rows[0][0] = 10

    with pytest.raises(BoardError):
        Board.from_rows(rows)


def test_valid_move_allowed_on_empty_cell():
    board = Board.from_rows(STARTING_ROWS)

    assert board.is_valid_move(row=0, col=2, value=4)


def test_move_rejected_when_value_exists_in_row_column_or_box():
    board = Board.from_rows(STARTING_ROWS)

    assert not board.is_valid_move(row=0, col=2, value=5)
    assert not board.is_valid_move(row=0, col=2, value=8)
    assert not board.is_valid_move(row=0, col=2, value=9)


def test_move_rejected_on_filled_cell():
    board = Board.from_rows(STARTING_ROWS)

    assert not board.is_valid_move(row=0, col=0, value=1)


def test_place_returns_new_board_without_mutating_original():
    board = Board.from_rows(STARTING_ROWS)

    updated = board.place(row=0, col=2, value=4)

    assert board.value_at(0, 2) == 0
    assert updated.value_at(0, 2) == 4


def test_invalid_place_raises_board_error():
    board = Board.from_rows(STARTING_ROWS)

    with pytest.raises(BoardError):
        board.place(row=0, col=2, value=5)


def test_valid_state_detects_duplicate_non_zero_values():
    valid = Board.from_rows(STARTING_ROWS)
    invalid_rows = [row[:] for row in STARTING_ROWS]
    invalid_rows[0][2] = 5
    invalid = Board.from_rows(invalid_rows)

    assert valid.is_valid_state()
    assert not invalid.is_valid_state()
