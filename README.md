# Adaptive Sudoku Web Application

A premium, responsive Sudoku web game that tracks your skill and challenges you dynamically using an adaptive rating engine. Originally designed as a Python CLI, this project has been fully wrapped in a modern, lightweight web layer.

The core game engine operates on **Test-Driven Development (TDD)** principles, utilizing immutable data structures for robust, bug-free game states.

---

## Key Features

### 🎮 Premium Solving Arena
*   **Intuitive Grid Interactivity:** Fluid cell selection with arrow keys and mouse.
*   **Pencil Notes Mode:** Write small candidate helpers inside cells using a mini 3x3 layout.
*   **Smart Eraser & Keypad:** Easily clear values with Backspace/Delete, or use a custom touch-friendly numerical keypad designed for mobile solvers.
*   **Instant Rule-Violation Rejections:** Immediate visual warnings (red shake animations) if you try to place duplicates in rows, columns, or 3x3 boxes.
*   **Non-Intrusive Mistakes:** Feel free to place incorrect numbers (without obtrusive duplicate conflicts) to check them later; mistakes do not penalize your live score.

### 🧠 Adaptive Skill Engine
*   **Personalized Ratings:** Start by selecting your initial difficulty (Beginner, Easy, Medium, Hard, Expert) to establish your baseline score (0, 20, 40, 60, 80).
*   **Automated Scaling Adjustments:** Your score dynamically increases or decreases based on completion time and hint counts using the adaptive player model.
*   **Invalid Attempt Penalties:** Obvious duplicate rule violations deduct `0.5` points per attempt (rounded at completion).
*   **Restart Resignations:** Clicking the **[ Resign Game ]** button abandons the current grid, applying a standard incomplete penalty (`-6` points) and showing your drops.
*   **Logical Boundary Mapping:** Smooth tier progression using strict inequality boundaries:
    *   **Beginner:** Score $< 20$ (Starting: 0)
    *   **Easy:** Score $20 \le \text{Score} < 40$ (Starting: 20)
    *   **Medium:** Score $40 \le \text{Score} < 60$ (Starting: 40)
    *   **Hard:** Score $60 \le \text{Score} < 80$ (Starting: 60)
    *   **Expert:** Score $\ge 80$ (Starting: 80)

### 🏆 Leaderboard & Rankings
*   **Skill Rank Index (SRI):** Qualifiers (solvers with at least 3 completed games) are ranked dynamically using the custom formula:  
    $$\text{SRI} = \text{skill\_score} + (\sqrt{\text{games\_played}} \times 2)$$
*   **Offline Rank Notifications:** If another player climbs past you on the leaderboard while you are offline, you will receive a custom alert banner on your next login!
*   **Consistent Visual Tier Display:** The difficulty tier shown next to your rating on the dashboard and leaderboard matches your actual displayed score (SRI or Skill score) rather than lagging behind the raw MMR.

### 🔒 Accounts & Preferences
*   **Secure Authentication:** User signup and login sessions backed by salted Bcrypt password hashes and session cookies.
*   **Persistent In-Progress Games:** If you log out or close the browser mid-session, the grid and timer are stored securely. Resume exactly where you left off.
*   **User Preferences:** Toggle light/dark themes, the active game timer, and real-time error highlight borders in Settings.

---

## Project Architecture

```text
Sudoku/
├── src/sudoku/                  # Core Sudoku Game Engine (Python)
│   ├── board.py                 # Immutable 9x9 board data structure
│   ├── solver.py                # Backtracking solver with MRV heuristics
│   ├── generator.py             # Puzzle generation with unique solvability
│   ├── puzzle.py                # Puzzle metadata container
│   ├── game.py                  # Immutable active session logic
│   ├── player_model.py          # Skill rating & performance deltas
│   ├── difficulty.py            # Difficulty bounds and scale mappings
│   └── storage.py               # Local CLI JSON persistence (legacy)
│
├── web/                         # Modern Web Application Layer
│   ├── __init__.py              # Flask app factory, blueprints & session managers
│   ├── config.py                # App environment properties
│   ├── models.py                # Relational SQLAlchemy SQLite schemas
│   ├── auth.py                  # Signup, login, logout controllers
│   ├── routes.py                # Main pages: home dashboard, settings, leaderboard
│   ├── game_routes.py           # Game plays, API handlers, victory redirectors
│   ├── templates/               # Jinja2 server-rendered views
│   └── static/                  # Static assets (frosted glass themes, JS event handlers)
│
├── tests/                       # Automated Test Suites
│   ├── test_board.py            # Core board validations tests
│   ├── test_solver.py           # Core solver checks tests
│   ├── test_generator.py        # Core generator unique checks tests
│   ├── test_game.py             # Core game actions tests
│   ├── test_player_model.py     # Core player ratings tests
│   └── test_web.py              # Web application integration TDD suite
│
├── instance/                    # SQLite database directory (auto-created)
├── requirements.txt             # Project library dependencies
├── run.py                       # Main Flask web entry point
├── pyproject.toml               # Project metadata configurations
└── README.md                    # This instruction documentation
```

---

## Installation & Running Locally

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/nulllvector/adaptive-sudoku-cli.git
    cd adaptive-sudoku-cli
    ```

2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Flask application:**
    ```bash
    python run.py
    ```

4.  **Play the game:**  
    Open your browser and navigate to `http://127.0.0.1:5000/`

---

## Running the Tests

To verify that both the core engine and the web application tests pass:

```bash
python -m pytest tests/
```

---

## Technologies Used

*   **Core Backend:** Python 3, Flask, Flask-Login, Flask-SQLAlchemy, Bcrypt
*   **Database:** SQLite
*   **Frontend Interactivity:** HTML5 (Jinja2 templates), Vanilla CSS (glassmorphism/dark themes), Vanilla JavaScript (grid keyboard/mouse listeners)
*   **Testing:** Pytest