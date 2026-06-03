import threading
import time
import pytest
import json
from playwright.sync_api import Page, expect
from web import create_app
from web.models import db, User, Profile, Game
from tests.test_web import TestConfig

@pytest.fixture(scope="session")
def app():
    app = create_app(TestConfig)
    return app

@pytest.fixture(scope="session")
def live_server(app):
    from werkzeug.serving import make_server
    server = make_server('127.0.0.1', 5001, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)
    yield "http://127.0.0.1:5001"
    server.shutdown()
    thread.join()

@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()

def test_medium_mode_onboarding_and_mistakes_restriction(page: Page, live_server: str, app):
    """
    Playwright browser test:
    1. Register user.
    2. Login user.
    3. Select MEDIUM difficulty in onboarding.
    4. Start a new game and assert difficulty is MEDIUM.
    5. Place a wrong number in the grid and assert it does NOT highlight as error.
    """
    # 1. Registration
    page.goto(f"{live_server}/register")
    page.fill("#username", "playwright_user")
    page.fill("#password", "password123")
    page.click("button[type='submit']")
    
    # Registration auto-logs in and redirects to home
    expect(page).to_have_url(f"{live_server}/home")
    
    # 2. Check onboarding difficulty is visible and select MEDIUM
    expect(page.locator("h2.card-title", has_text="Select Starting Difficulty")).to_be_visible()
    
    # Check the MEDIUM radio option and submit
    page.check("input[name='difficulty'][value='MEDIUM']")
    page.click("#lock-difficulty-btn")
    
    # Redirected back to home page, Play card is active
    expect(page).to_have_url(f"{live_server}/home")
    expect(page.locator("#stat-difficulty")).to_have_text("medium")
    
    # 3. Start game
    page.click("#play-button")
    expect(page).to_have_url(f"{live_server}/game")
    
    # Assert difficulty badge says MEDIUM
    expect(page.locator(".difficulty-badge")).to_have_text("MEDIUM")
    
    # 4. Find first empty cell (given cell is not player-editable)
    # We retrieve the solution from window.gameData to know a wrong value to enter
    game_data = page.evaluate("window.gameData")
    solution = game_data["solution"]
    initial_board = game_data["initial_board"]
    
    selected_r, selected_c, wrong_value = None, None, None
    for r in range(9):
        for c in range(9):
            if initial_board[r][c] == 0:
                # Find values in row
                row_vals = {initial_board[r][i] for i in range(9) if initial_board[r][i] != 0}
                # Find values in col
                col_vals = {initial_board[i][c] for i in range(9) if initial_board[i][c] != 0}
                # Find values in box
                box_r, box_c = 3 * (r // 3), 3 * (c // 3)
                box_vals = {
                    initial_board[box_r + i][box_c + j]
                    for i in range(3)
                    for j in range(3)
                    if initial_board[box_r + i][box_c + j] != 0
                }
                
                allowed_vals = set(range(1, 10)) - row_vals - col_vals - box_vals
                correct_val = solution[r][c]
                wrong_vals = allowed_vals - {correct_val}
                
                if wrong_vals:
                    selected_r, selected_c = r, c
                    wrong_value = list(wrong_vals)[0]
                    break
        if selected_r is not None:
            break
            
    assert selected_r is not None
    r, c = selected_r, selected_c
    
    # Click the cell in the grid
    page.click(f"#cell-{r}-{c}")
    
    # Press key pad or keyboard input to place the wrong value
    # We will simulate keyboard press of the wrong value
    page.keyboard.press(str(wrong_value))
    
    # Wait a moment for network/UI updates
    time.sleep(0.5)
    
    # Verify the value container contains the wrong value
    cell_value_locator = page.locator(f"#cell-{r}-{c} .cell-value")
    expect(cell_value_locator).to_have_text(str(wrong_value))
    
    # Verify that the cell does NOT have the 'error-cell' class (no mistake highlights in Medium+ mode)
    cell_locator = page.locator(f"#cell-{r}-{c}")
    expect(cell_locator).not_to_have_class("error-cell")


def test_optimistic_ui_updates(page: Page, live_server: str, app):
    """
    Playwright browser test for Optimistic UI updates:
    Verify that typing a value displays it on the board immediately (0ms)
    even when the backend API response is delayed by a slow network.
    """
    # 1. Register and login
    page.goto(f"{live_server}/register")
    page.fill("#username", "optimistic_user")
    page.fill("#password", "password123")
    page.click("button[type='submit']")
    
    # 2. Select EASY onboarding
    page.check("input[name='difficulty'][value='EASY']")
    page.click("#lock-difficulty-btn")
    
    # 3. Start game
    page.click("#play-button")
    expect(page).to_have_url(f"{live_server}/game")
    
    # 4. Set up request interception for /game/api/move to delay it by 2.0 seconds in JS
    page.evaluate("""
        const originalFetch = window.fetch;
        window.fetch = async function(...args) {
            if (args[0] === '/game/api/move' || (typeof args[0] === 'string' && args[0].includes('/game/api/move'))) {
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
            return originalFetch(...args);
        };
    """)
    
    # Get game grid states
    game_data = page.evaluate("window.gameData")
    initial_board = game_data["initial_board"]
    solution = game_data["solution"]
    
    # Find an empty cell
    r, c = None, None
    for row in range(9):
        for col in range(9):
            if initial_board[row][col] == 0:
                r, c = row, col
                break
        if r is not None:
            break
            
    assert r is not None
    
    # 5. Click the cell and input correct solution value
    page.click(f"#cell-{r}-{c}")
    val_to_press = solution[r][c]
    
    # Record the time before input
    import time
    start_input = time.time()
    page.keyboard.press(str(val_to_press))
    
    # 6. Assert that the value appears IMMEDIATELY (well before 2 seconds)
    cell_value_locator = page.locator(f"#cell-{r}-{c} .cell-value")
    # Wait briefly to let the UI thread execute, but far less than 2.0s
    page.wait_for_timeout(100)
    
    expect(cell_value_locator).to_have_text(str(val_to_press))
    elapsed_time = time.time() - start_input
    
    # The elapsed time for rendering must be very low (< 0.5 seconds)
    assert elapsed_time < 0.5, f"Optimistic UI update took too long: {elapsed_time}s"


