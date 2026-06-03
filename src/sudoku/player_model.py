from __future__ import annotations

from dataclasses import dataclass

from sudoku.difficulty import Difficulty, difficulty_for_skill, step_toward


@dataclass(frozen=True)
class GameResult:
    completed: bool
    elapsed_seconds: int
    mistakes: int
    hints_used: int
    invalid_attempts: int
    filled_cells: int


@dataclass(frozen=True)
class PlayerProfile:
    skill_score: int = 25
    current_difficulty: Difficulty = Difficulty.EASY
    games_played: int = 0

    def record_result(self, result: GameResult) -> "PlayerProfile":
        score_delta = _score_delta(result)
        next_score = max(0, min(100, self.skill_score + score_delta))
        target_difficulty = difficulty_for_skill(next_score)
        next_difficulty = step_toward(self.current_difficulty, target_difficulty)

        return PlayerProfile(
            skill_score=next_score,
            current_difficulty=next_difficulty,
            games_played=self.games_played + 1,
        )


def _score_delta(result: GameResult) -> int:
    delta = 0

    if result.completed:
        delta += 8
    else:
        delta -= 6

    delta -= result.mistakes
    delta -= result.hints_used * 3
    delta -= result.invalid_attempts

    if result.completed and result.filled_cells > 0:
        seconds_per_cell = result.elapsed_seconds / result.filled_cells
        if seconds_per_cell <= 20:
            delta += 6
        elif seconds_per_cell <= 45:
            delta += 2
        elif seconds_per_cell >= 120:
            delta -= 4

    return delta
