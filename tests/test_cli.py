import pytest

from sudoku.board import Board
from sudoku.cli import _parse_move, format_board


def test_parse_move_converts_user_friendly_numbers_to_zero_based_indexes():
    assert _parse_move("1 3 4") == (0, 2, 4)


def test_parse_move_rejects_bad_input():
    with pytest.raises(ValueError):
        _parse_move("1 2")

    with pytest.raises(ValueError):
        _parse_move("10 1 1")


def test_format_board_shows_empty_cells_as_dots():
    board = Board.empty()

    rendered = format_board(board, board)

    assert "." in rendered
    assert "+-------+-------+-------+" in rendered
