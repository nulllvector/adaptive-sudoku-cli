from __future__ import annotations

import time
from pathlib import Path

from sudoku.board import BoardError
from sudoku.game import GameSession
from sudoku.generator import generate_puzzle
from sudoku.player_model import GameResult
from sudoku.storage import load_profile, save_profile


PROFILE_PATH = Path("player_profile.json")


def main() -> None:
    profile = load_profile(PROFILE_PATH)
    puzzle = generate_puzzle(profile.current_difficulty)
    session = GameSession.start(puzzle)
    started_at = time.monotonic()

    print("Adaptive Sudoku CLI")
    print(f"Difficulty: {profile.current_difficulty.name.title()}")
    print("Enter moves as: row col value. Example: 1 3 4")
    print("Commands: hint, quit")

    while not session.is_won():
        print()
        print(format_board(session.board, puzzle.starting_board))
        command = input("> ").strip().lower()

        if command in {"q", "quit", "exit"}:
            break

        if command == "hint":
            session = session.use_hint()
            continue

        try:
            row, col, value = _parse_move(command)
            session = session.make_move(row, col, value)
        except (BoardError, ValueError) as error:
            session = session.record_invalid_attempt()
            print(f"Invalid input: {error}")
            continue

        if session.mistakes:
            print(f"Mistakes: {session.mistakes}")

    elapsed_seconds = int(time.monotonic() - started_at)
    completed = session.is_won()
    result = GameResult(
        completed=completed,
        elapsed_seconds=elapsed_seconds,
        mistakes=session.mistakes,
        hints_used=session.hints_used,
        invalid_attempts=session.invalid_attempts,
        filled_cells=_filled_player_cells(session),
    )
    updated_profile = profile.record_result(result)
    save_profile(PROFILE_PATH, updated_profile)

    print()
    print(format_board(session.board, puzzle.starting_board))
    if completed:
        print("Solved. Nice work.")
    else:
        print("Game saved to your profile as incomplete.")
    print(f"Skill score: {profile.skill_score} -> {updated_profile.skill_score}")
    print(f"Next difficulty: {updated_profile.current_difficulty.name.title()}")


def format_board(board, starting_board) -> str:
    lines: list[str] = []
    separator = "+-------+-------+-------+"

    for row in range(9):
        if row % 3 == 0:
            lines.append(separator)

        cells = []
        for col in range(9):
            value = board.value_at(row, col)
            label = "." if value == 0 else str(value)
            if not starting_board.is_empty(row, col):
                label = label
            cells.append(label)

        lines.append(
            "| "
            + " ".join(cells[0:3])
            + " | "
            + " ".join(cells[3:6])
            + " | "
            + " ".join(cells[6:9])
            + " |"
        )

    lines.append(separator)
    return "\n".join(lines)


def _parse_move(command: str) -> tuple[int, int, int]:
    parts = command.split()
    if len(parts) != 3:
        raise ValueError("use three numbers: row col value.")

    row, col, value = (int(part) for part in parts)
    if not 1 <= row <= 9 or not 1 <= col <= 9 or not 1 <= value <= 9:
        raise ValueError("row, column, and value must be from 1 to 9.")

    return row - 1, col - 1, value


def _filled_player_cells(session: GameSession) -> int:
    filled = 0
    for row in range(9):
        for col in range(9):
            if session.puzzle.is_given(row, col):
                continue
            if not session.board.is_empty(row, col):
                filled += 1
    return filled
