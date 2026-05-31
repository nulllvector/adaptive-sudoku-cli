from sudoku.difficulty import Difficulty
from sudoku.player_model import GameResult, PlayerProfile


def test_strong_completed_game_increases_skill_score():
    profile = PlayerProfile(skill_score=35, current_difficulty=Difficulty.EASY)
    result = GameResult(
        completed=True,
        elapsed_seconds=600,
        mistakes=0,
        hints_used=0,
        invalid_attempts=0,
        filled_cells=40,
    )

    updated = profile.record_result(result)

    assert updated.skill_score > profile.skill_score
    assert updated.games_played == 1


def test_poor_game_decreases_skill_score():
    profile = PlayerProfile(skill_score=50, current_difficulty=Difficulty.MEDIUM)
    result = GameResult(
        completed=False,
        elapsed_seconds=1200,
        mistakes=4,
        hints_used=3,
        invalid_attempts=5,
        filled_cells=12,
    )

    updated = profile.record_result(result)

    assert updated.skill_score < profile.skill_score


def test_adaptive_difficulty_changes_gradually():
    profile = PlayerProfile(skill_score=75, current_difficulty=Difficulty.BEGINNER)
    result = GameResult(
        completed=True,
        elapsed_seconds=300,
        mistakes=0,
        hints_used=0,
        invalid_attempts=0,
        filled_cells=45,
    )

    updated = profile.record_result(result)

    assert updated.current_difficulty == Difficulty.EASY
