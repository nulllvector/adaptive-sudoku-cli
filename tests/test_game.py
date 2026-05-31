import pytest

from sudoku.board import Board, BoardError
from sudoku.difficulty import Difficulty
from sudoku.game import GameSession
from sudoku.puzzle import Puzzle


STARTING_ROWS = [
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

SOLUTION_ROWS = [row[:] for row in STARTING_ROWS]
STARTING_ROWS[0][2] = 0


def make_one_move_puzzle() -> Puzzle:
    return Puzzle(
        starting_board=Board.from_rows(STARTING_ROWS),
        solution=Board.from_rows(SOLUTION_ROWS),
        difficulty=Difficulty.BEGINNER,
    )


def test_valid_game_move_updates_board():
    session = GameSession.start(make_one_move_puzzle())

    updated = session.make_move(row=0, col=2, value=4)

    assert updated.board.value_at(0, 2) == 4
    assert updated.mistakes == 0


def test_wrong_game_move_counts_mistake_without_changing_board():
    session = GameSession.start(make_one_move_puzzle())

    updated = session.make_move(row=0, col=2, value=1)

    assert updated.board.value_at(0, 2) == 0
    assert updated.mistakes == 1


def test_given_cell_cannot_be_changed():
    session = GameSession.start(make_one_move_puzzle())

    with pytest.raises(BoardError):
        session.make_move(row=0, col=0, value=4)


def test_hint_fills_first_empty_cell_and_counts_usage():
    session = GameSession.start(make_one_move_puzzle())

    updated = session.use_hint()

    assert updated.board.value_at(0, 2) == 4
    assert updated.hints_used == 1
    assert updated.is_won()


def test_invalid_attempt_can_be_recorded():
    session = GameSession.start(make_one_move_puzzle())

    updated = session.record_invalid_attempt()

    assert updated.invalid_attempts == 1
