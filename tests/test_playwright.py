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
