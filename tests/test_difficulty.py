from sudoku.difficulty import Difficulty, difficulty_for_skill, step_toward


def test_skill_score_maps_to_difficulty_bucket():
    assert difficulty_for_skill(0) == Difficulty.BEGINNER
    assert difficulty_for_skill(21) == Difficulty.EASY
    assert difficulty_for_skill(41) == Difficulty.MEDIUM
    assert difficulty_for_skill(61) == Difficulty.HARD
    assert difficulty_for_skill(81) == Difficulty.EXPERT


def test_difficulty_moves_one_step_at_a_time():
    assert step_toward(Difficulty.EASY, Difficulty.EXPERT) == Difficulty.MEDIUM
    assert step_toward(Difficulty.HARD, Difficulty.BEGINNER) == Difficulty.MEDIUM
    assert step_toward(Difficulty.MEDIUM, Difficulty.MEDIUM) == Difficulty.MEDIUM
