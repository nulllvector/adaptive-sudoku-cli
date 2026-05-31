# Adaptive Sudoku CLI

A Python command-line Sudoku game built using Test-Driven Development (TDD).

The long-term goal of this project is to create an adaptive Sudoku experience that adjusts puzzle difficulty based on player skill and behavior. Instead of relying only on fixed difficulty levels, the game will eventually analyze player performance and dynamically select puzzles that provide an appropriate challenge.

## Features

### Implemented

* Sudoku board representation
* Move validation
* Unit tests using Pytest
* TDD-based development workflow

### Planned

* Sudoku solver with uniqueness checks
* Puzzle generation by difficulty
* Interactive command-line interface
* Player skill tracking
* Adaptive difficulty selection
* Save and load functionality

## Installation

```bash
git clone https://github.com/nulllvector/adaptive-sudoku-cli.git
cd adaptive-sudoku-cli
pip install -e .
```

## Running Tests

```bash
python -m pytest
```

## Project Structure

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

## Development Process

This project follows the Test-Driven Development (TDD) cycle:

1. Write a failing test.
2. Implement the smallest amount of code needed to pass.
3. Refactor while keeping all tests green.

## Roadmap

1. Complete board validation and game rules.
2. Implement a Sudoku solver.
3. Generate puzzles with guaranteed unique solutions.
4. Build a playable CLI experience.
5. Add player analytics and adaptive difficulty.
6. Improve persistence and user profiles.

## License

This project is currently for learning and experimentation.