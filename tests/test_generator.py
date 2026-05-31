import random

from sudoku.difficulty import Difficulty, GIVEN_RANGES
from sudoku.generator import generate_puzzle, generate_solved_board
from sudoku.solver import has_unique_solution


def test_generated_solved_board_is_complete_and_valid():
    board = generate_solved_board(random.Random(1))

    assert board.is_complete()
    assert board.is_valid_state()


def test_generated_puzzle_has_unique_solution():
    puzzle = generate_puzzle(Difficulty.BEGINNER, random.Random(2))

    assert has_unique_solution(puzzle.starting_board)
    assert puzzle.solution.is_complete()
    assert puzzle.solution.is_valid_state()


def test_generated_puzzle_respects_difficulty_given_range():
    puzzle = generate_puzzle(Difficulty.BEGINNER, random.Random(3))

    assert puzzle.given_count in GIVEN_RANGES[Difficulty.BEGINNER]
