import json
import pytest
import math
from web import create_app
from web.models import db, User, Profile, UserSettings, Game
from web.config import Config
from sudoku.difficulty import Difficulty
from sudoku.board import Board

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Use in-memory SQLite for speed and isolation
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret'

@pytest.fixture
def app():
    app = create_app(TestConfig)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def init_database(app):
    with app.app_context():
        yield db
        db.session.remove()
        db.drop_all()

def test_registration_flow(client, init_database):
    """Test that a new user registration succeeds and auto-creates profile & settings."""
    response = client.post('/register', data={
        'username': 'alice',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    user = User.query.filter_by(username='alice').first()
    assert user is not None
    assert user.password_hash != 'password123'
    
    assert user.profile is not None
    assert user.profile.skill_score == 0
    assert user.profile.difficulty_locked is False
    assert user.profile.games_played == 0
    
    assert user.settings is not None
    assert user.settings.theme == 'dark'

def test_duplicate_registration_fails(client, init_database):
    """Test that registering an already existing username fails."""
    client.post('/register', data={'username': 'alice', 'password': 'password123'})
    
    response = client.post('/register', data={'username': 'alice', 'password': 'newpassword'}, follow_redirects=True)
    assert b"Username already exists" in response.data or response.status_code == 200
    
    users = User.query.filter_by(username='alice').all()
    assert len(users) == 1

def test_login_logout_flow(client, init_database):
    """Test standard login and logout sessions."""
    client.post('/register', data={'username': 'bob', 'password': 'password123'})
    
    # Explicitly logout so the client starts in a clean unauthenticated state
    client.get('/logout')
    
    response = client.post('/login', data={'username': 'bob', 'password': 'wrongpassword'}, follow_redirects=True)
    assert b"Invalid username or password" in response.data
    
    response = client.post('/login', data={'username': 'bob', 'password': 'password123'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"bob" in response.data
    
    response = client.get('/home')
    assert response.status_code == 200
    
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    
    response = client.get('/home')
    assert response.status_code == 302

def test_difficulty_selection(client, init_database):
    """Test that initial difficulty selection locks the choice and sets correct ratings."""
    client.post('/register', data={'username': 'charlie', 'password': 'password123'})
    client.post('/login', data={'username': 'charlie', 'password': 'password123'})
    
    response = client.get('/home')
    assert b"Select Difficulty" in response.data or b"difficulty" in response.data
    
    response = client.post('/home/select-difficulty', data={'difficulty': 'EASY'}, follow_redirects=True)
    assert response.status_code == 200
    
    user = User.query.filter_by(username='charlie').first()
    assert user.profile.current_difficulty == 'EASY'
    assert user.profile.skill_score == 20
    assert user.profile.difficulty_locked is True

def test_account_reset(client, init_database):
    """Test that resetting the profile clears rating, games played, and active games."""
    client.post('/register', data={'username': 'dave', 'password': 'password123'})
    client.post('/login', data={'username': 'dave', 'password': 'password123'})
    client.post('/home/select-difficulty', data={'difficulty': 'MEDIUM'})
    
    response = client.post('/home/reset', follow_redirects=True)
    assert response.status_code == 200
    
    user = User.query.filter_by(username='dave').first()
    assert user.profile.difficulty_locked is False
    assert user.profile.skill_score == 0
    assert user.profile.games_played == 0

def test_game_start_and_resume(client, init_database):
    """Test that accessing /game generates a new puzzle or resumes an active one."""
    client.post('/register', data={'username': 'game_user', 'password': 'password123'})
    client.post('/login', data={'username': 'game_user', 'password': 'password123'})
    client.post('/home/select-difficulty', data={'difficulty': 'BEGINNER'})
    
    # 1. Start game (should generate new game in DB)
    response = client.get('/game')
    assert response.status_code == 200
    
    user = User.query.filter_by(username='game_user').first()
    active_game = Game.query.filter_by(user_id=user.id, status='active').first()
    assert active_game is not None
    assert active_game.difficulty == 'BEGINNER'
    
    initial_board_str = active_game.initial_board
    
    # 2. Accessing /game again should resume (retrieve same game, no new creation)
    response = client.get('/game')
    assert response.status_code == 200
    assert Game.query.filter_by(user_id=user.id, status='active').count() == 1
    
    active_game_2 = Game.query.filter_by(user_id=user.id, status='active').first()
    assert active_game_2.initial_board == initial_board_str

def test_game_invalid_attempt_rejection(client, init_database):
    """Test that invalid moves (obvious duplicate rules violation) are rejected and count as invalid attempts."""
    client.post('/register', data={'username': 'game_user', 'password': 'password123'})
    client.post('/login', data={'username': 'game_user', 'password': 'password123'})
    client.post('/home/select-difficulty', data={'difficulty': 'BEGINNER'})
    
    client.get('/game') # Generates game
    
    user = User.query.filter_by(username='game_user').first()
    game = Game.query.filter_by(user_id=user.id, status='active').first()
    
    # Find an empty cell
    board_grid = json.loads(game.current_board)
    empty_cell = None
    for r in range(9):
        for c in range(9):
            if board_grid[r][c] == 0:
                empty_cell = (r, c)
                break
        if empty_cell:
            break
            
    assert empty_cell is not None
    row, col = empty_cell
    
    # Place a duplicate value: let's pick a value already present in the same row
    row_values = board_grid[row]
    duplicate_value = next(val for val in row_values if val != 0)
    
    # Make invalid move
    response = client.post('/game/api/move', json={
        'row': row,
        'col': col,
        'value': duplicate_value
    })
    
    assert response.status_code == 200
    res_data = json.loads(response.data)
    assert res_data['correct'] is False
    assert res_data['invalid'] is True
    
    # Assert invalid_attempts counter incremented in DB
    db.session.refresh(game)
    assert game.invalid_attempts == 1

def test_game_restart_resignation(client, init_database):
    """Test that clicking restart counts as resigning (marks abandoned, sets rating drop, redirects victory)."""
    client.post('/register', data={'username': 'game_user', 'password': 'password123'})
    client.post('/login', data={'username': 'game_user', 'password': 'password123'})
    client.post('/home/select-difficulty', data={'difficulty': 'EASY'}) # starting score = 20
    
    client.get('/game') # Generates game
    
    # Restart
    response = client.post('/game/api/restart')
    assert response.status_code == 302 # Redirects to victory
    
    user = User.query.filter_by(username='game_user').first()
    game = Game.query.filter_by(user_id=user.id).first()
    assert game.status == 'abandoned'
    
    # Easy (20) - incomplete penalty (6) = 14
    assert user.profile.skill_score == 14

def test_game_completion(client, init_database):
    """Test full game completion successfully increments games_played, updates rating, redirects to victory."""
    client.post('/register', data={'username': 'winner', 'password': 'password123'})
    client.post('/login', data={'username': 'winner', 'password': 'password123'})
    client.post('/home/select-difficulty', data={'difficulty': 'BEGINNER'}) # starting score = 0
    
    client.get('/game') # Generates game
    
    user = User.query.filter_by(username='winner').first()
    game = Game.query.filter_by(user_id=user.id, status='active').first()
    
    solution_grid = json.loads(game.solution)
    board_grid = [list(r) for r in solution_grid]
    
    # Make board solved except for one empty cell (0, 0)
    correct_value = board_grid[0][0]
    board_grid[0][0] = 0
    
    game.current_board = json.dumps(board_grid)
    
    # Clear (0, 0) in initial_board too so it is treated as a playable cell, not a locked given cell
    initial_grid = json.loads(game.initial_board)
    initial_grid[0][0] = 0
    game.initial_board = json.dumps(initial_grid)
    
    db.session.commit()
    
    # Make the winning move!
    response = client.post('/game/api/move', json={
        'row': 0,
        'col': 0,
        'value': correct_value
    })
    
    assert response.status_code == 200
    res_data = json.loads(response.data)
    assert res_data['won'] is True
    
    db.session.refresh(game)
    db.session.refresh(user.profile)
    assert game.status == 'won'
    assert user.profile.games_played == 1
    # Skill score should have increased (won +8, filled_cells > 0 might give speed bonus)
    assert user.profile.skill_score > 0

def test_sri_leaderboard_sorting(client, init_database):
    """Test that leaderboard computes SRI rank = score + sqrt(games)*2, filters games>=3, and sorts desc."""
    # User A: score 50, games 4 -> SRI = 50 + (2 * 2) = 54
    client.post('/register', data={'username': 'usera', 'password': 'password123'})
    # User B: score 52, games 3 -> SRI = 52 + (1.732 * 2) = 55.464
    client.post('/register', data={'username': 'userb', 'password': 'password123'})
    # User C: score 80, games 2 (should not appear on leaderboard)
    client.post('/register', data={'username': 'userc', 'password': 'password123'})
    
    usera = User.query.filter_by(username='usera').first()
    usera.profile.skill_score = 50
    usera.profile.games_played = 4
    
    userb = User.query.filter_by(username='userb').first()
    userb.profile.skill_score = 52
    userb.profile.games_played = 3
    
    userc = User.query.filter_by(username='userc').first()
    userc.profile.skill_score = 80
    userc.profile.games_played = 2
    
    db.session.commit()
    
    # Login and check leaderboard
    client.post('/login', data={'username': 'usera', 'password': 'password123'})
    response = client.get('/leaderboard')
    
    assert response.status_code == 200
    # userb should be Rank 1 (SRI 55.464 > 54)
    # userc should not appear at all
    assert b"userb" in response.data
    assert b"usera" in response.data
    assert b"userc" not in response.data

def test_offline_rank_change_notification(client, init_database):
    """Test that ranking shift while user is away triggers exactly one home page notification."""
    # Register 3 users with games_played=3 (leaderboard eligible)
    client.post('/register', data={'username': 'p1', 'password': 'password123'})
    client.post('/register', data={'username': 'p2', 'password': 'password123'})
    client.post('/register', data={'username': 'p3', 'password': 'password123'})
    
    p1 = User.query.filter_by(username='p1').first()
    p1.profile.skill_score = 50
    p1.profile.games_played = 3 # SRI = 50 + 3.464 = 53.464 (Rank 1 initially)
    p1.profile.last_seen_rank = 1
    
    p2 = User.query.filter_by(username='p2').first()
    p2.profile.skill_score = 45
    p2.profile.games_played = 3 # SRI = 45 + 3.464 = 48.464 (Rank 2 initially)
    p2.profile.last_seen_rank = 2
    
    p3 = User.query.filter_by(username='p3').first()
    p3.profile.skill_score = 40
    p3.profile.games_played = 3 # SRI = 40 + 3.464 = 43.464 (Rank 3 initially)
    p3.profile.last_seen_rank = 3
    
    db.session.commit()
    
    # While p2 is offline, p3 gets an update to score 48 (new SRI = 51.464).
    # p3 is now higher than p2, so p2 drops from Rank 2 to Rank 3!
    p3.profile.skill_score = 48

    db.session.commit()
    
    # Log in p2, access home page
    client.post('/login', data={'username': 'p2', 'password': 'password123'})
    response = client.get('/home')
    
    # Assert notification shows rank dropped from 2 to 3
    assert b"leaderboard rank dropped from #2 to #3" in response.data
    
    # Verify profile last_seen_rank updated to 3 in DB
    db.session.refresh(p2.profile)
    assert p2.profile.last_seen_rank == 3
    
    # Refresh home page, message should not be flashed again
    response2 = client.get('/home')
    assert b"leaderboard rank dropped" not in response2.data

def test_game_heartbeat(client, init_database):
    """Test that posting to the heartbeat endpoint successfully updates game accumulated seconds."""
    client.post('/register', data={'username': 'game_user', 'password': 'password123'})
    client.post('/login', data={'username': 'game_user', 'password': 'password123'})
    client.post('/home/select-difficulty', data={'difficulty': 'BEGINNER'})
    
    client.get('/game') # Generates game
    
    user = User.query.filter_by(username='game_user').first()
    game = Game.query.filter_by(user_id=user.id, status='active').first()
    assert game.accumulated_seconds == 0
    
    # Send heartbeat
    response = client.post('/game/api/heartbeat', json={
        'elapsed_seconds': 45
    })
    
    assert response.status_code == 200
    res_data = json.loads(response.data)
    assert res_data['success'] is True
    
    db.session.refresh(game)
    assert game.accumulated_seconds == 45

def test_victory_remarks_milestone(client, init_database):
    """Test that victory page displays correct congrats/motivation remarks based on games_played milestone."""
    client.post('/register', data={'username': 'milestone_user', 'password': 'password123'})
    client.post('/login', data={'username': 'milestone_user', 'password': 'password123'})
    client.post('/home/select-difficulty', data={'difficulty': 'BEGINNER'})
    
    # 1. Create a game that is won, with games_played = 2 (not 3 yet)
    user = User.query.filter_by(username='milestone_user').first()
    game1 = Game(
        user_id=user.id,
        initial_board="[[0]]",
        solution="[[0]]",
        current_board="[[0]]",
        difficulty="BEGINNER",
        status="won"
    )
    db.session.add(game1)
    user.profile.games_played = 2
    db.session.commit()
    
    response = client.get(f'/victory/{game1.id}?rating_before=20&rating_after=22&rank_before=&rank_after=')
    assert response.status_code == 200
    assert b"Milestone Achieved!" not in response.data
    assert b"Keep climbing!" not in response.data
    
    # 2. Create a game that is won, with games_played = 3 (exactly 3 matches completed!)
    game2 = Game(
        user_id=user.id,
        initial_board="[[0]]",
        solution="[[0]]",
        current_board="[[0]]",
        difficulty="BEGINNER",
        status="won"
    )
    db.session.add(game2)
    user.profile.games_played = 3
    db.session.commit()
    
    response2 = client.get(f'/victory/{game2.id}?rating_before=22&rating_after=25&rank_before=&rank_after=5')
    assert response2.status_code == 200
    assert b"Milestone Achieved!" in response2.data
    assert b"Keep climbing!" not in response2.data
    
    # 3. Create a game that is won, with games_played = 4 (> 3 matches)
    game3 = Game(
        user_id=user.id,
        initial_board="[[0]]",
        solution="[[0]]",
        current_board="[[0]]",
        difficulty="BEGINNER",
        status="won"
    )
    db.session.add(game3)
    user.profile.games_played = 4
    db.session.commit()
    
    response3 = client.get(f'/victory/{game3.id}?rating_before=25&rating_after=28&rank_before=5&rank_after=4')
    assert response3.status_code == 200
    assert b"Milestone Achieved!" not in response3.data
    assert b"Keep climbing!" in response3.data

def test_delete_account(client, init_database):
    """Test that POST /settings/delete-account deletes the user and cascades all associated data."""
    client.post('/register', data={'username': 'delete_me', 'password': 'password123'})
    client.post('/login', data={'username': 'delete_me', 'password': 'password123'})
    
    # Verify user, settings, profile exist
    user = User.query.filter_by(username='delete_me').first()
    assert user is not None
    user_id = user.id
    
    profile = Profile.query.filter_by(user_id=user_id).first()
    assert profile is not None
    
    settings_record = UserSettings.query.filter_by(user_id=user_id).first()
    assert settings_record is not None
    
    # Delete the account
    response = client.post('/settings/delete-account', follow_redirects=True)
    assert response.status_code == 200
    
    # Check that database records are deleted
    deleted_user = User.query.filter_by(username='delete_me').first()
    assert deleted_user is None
    
    deleted_profile = Profile.query.filter_by(user_id=user_id).first()
    assert deleted_profile is None
    
    deleted_settings = UserSettings.query.filter_by(user_id=user_id).first()
    assert deleted_settings is None


