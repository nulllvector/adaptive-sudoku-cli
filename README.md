# Adaptive Sudoku

A Python CLI Sudoku project built with TDD. The first version focuses on a clean game core, then layers on adaptive difficulty based on observed player behavior.

## Roadmap

1. Board rules and validation.
2. Solver with uniqueness checks.
3. Puzzle generation by difficulty.
4. Playable CLI.
5. Player skill tracking and adaptive difficulty.

## TDD Workflow

```powershell
python -m pytest
```

For every feature:

1. Write a failing test.
2. Implement the smallest useful behavior.
3. Refactor with the tests passing.

## Architecture

```text
src/sudoku/
  board.py         Grid representation and move validation.
  solver.py        Solving and uniqueness checks.
  generator.py     Puzzle creation.
  puzzle.py        Puzzle metadata and givens.
  game.py          Active game session state.
  player_model.py  Skill estimation from player behavior.
  difficulty.py    Difficulty levels and selection.
  storage.py       Local profile and save data.
  cli.py           Terminal interface.
```
