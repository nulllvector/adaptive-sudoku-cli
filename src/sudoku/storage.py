from __future__ import annotations

import json
from pathlib import Path

from sudoku.difficulty import Difficulty
from sudoku.player_model import PlayerProfile


def save_profile(path: Path, profile: PlayerProfile) -> None:
    data = {
        "skill_score": profile.skill_score,
        "current_difficulty": profile.current_difficulty.name,
        "games_played": profile.games_played,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_profile(path: Path) -> PlayerProfile:
    if not path.exists():
        return PlayerProfile()

    data = json.loads(path.read_text(encoding="utf-8"))
    return PlayerProfile(
        skill_score=int(data["skill_score"]),
        current_difficulty=Difficulty[data["current_difficulty"]],
        games_played=int(data["games_played"]),
    )
