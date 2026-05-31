from __future__ import annotations

from enum import IntEnum


class Difficulty(IntEnum):
    BEGINNER = 0
    EASY = 1
    MEDIUM = 2
    HARD = 3
    EXPERT = 4


GIVEN_RANGES: dict[Difficulty, range] = {
    Difficulty.BEGINNER: range(45, 51),
    Difficulty.EASY: range(40, 45),
    Difficulty.MEDIUM: range(34, 40),
    Difficulty.HARD: range(28, 34),
    Difficulty.EXPERT: range(22, 28),
}


def difficulty_for_skill(score: int) -> Difficulty:
    score = max(0, min(100, score))
    if score <= 20:
        return Difficulty.BEGINNER
    if score <= 40:
        return Difficulty.EASY
    if score <= 60:
        return Difficulty.MEDIUM
    if score <= 80:
        return Difficulty.HARD
    return Difficulty.EXPERT


def step_toward(current: Difficulty, target: Difficulty) -> Difficulty:
    if target > current:
        return Difficulty(current + 1)
    if target < current:
        return Difficulty(current - 1)
    return current
