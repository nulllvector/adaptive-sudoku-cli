import json
import math
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from web.models import db, Game, Profile
from web.routes import get_leaderboard
from sudoku.generator import generate_puzzle
from sudoku.difficulty import Difficulty
from sudoku.board import Board
from sudoku.puzzle import Puzzle
from sudoku.game import GameSession
from sudoku.player_model import PlayerProfile, GameResult

game_bp = Blueprint('game', __name__)

@game_bp.route('/game')
@login_required
def game():
    # If the user has not locked their difficulty, redirect to home
    if not current_user.profile.difficulty_locked:
        flash('Please select a starting difficulty first.')
        return redirect(url_for('main.home'))
        
    # Check if there is an active game
    active_game = Game.query.filter_by(user_id=current_user.id, status='active').first()
    
    if not active_game:
        # Generate new puzzle
        diff = Difficulty[current_user.profile.current_difficulty]
        puzzle = generate_puzzle(diff)
        
        # Serialize boards to JSON
        initial_board = json.dumps(puzzle.starting_board.grid)
        solution = json.dumps(puzzle.solution.grid)
        current_board = json.dumps(puzzle.starting_board.grid)
        
        active_game = Game(
            user_id=current_user.id,
            initial_board=initial_board,
            solution=solution,
            current_board=current_board,
            difficulty=current_user.profile.current_difficulty,
            status='active',
            started_at=datetime.utcnow()
        )
        # Defensively mark any active games as abandoned to prevent lingering games / race conditions
        Game.query.filter_by(user_id=current_user.id, status='active').update({'status': 'abandoned'})
        db.session.add(active_game)
        db.session.commit()
    else:
        # Resume active game: reset starting clock to current UTC time
        active_game.started_at = datetime.utcnow()
        db.session.commit()
        
    return render_template('game.html', game=active_game, settings=current_user.settings)

@game_bp.route('/game/api/move', methods=['POST'])
@login_required
def move():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request body.'}), 400
        
    row = data.get('row')
    col = data.get('col')
    value = data.get('value')
    
    if row is None or col is None or value is None:
        return jsonify({'error': 'Missing row, col, or value.'}), 400
        
    # Get active game
    game = Game.query.filter_by(user_id=current_user.id, status='active').first()
    if not game:
        return jsonify({'error': 'No active game found.'}), 404
        
    initial_grid = json.loads(game.initial_board)
    current_grid = json.loads(game.current_board)
    solution_grid = json.loads(game.solution)
    
    # 1. Block editing of given cells
    if initial_grid[row][col] != 0:
        return jsonify({'correct': False, 'error': 'Cannot change a given cell.'}), 400
        
    # 2. Handle erasure (value = 0)
    if value == 0:
        current_grid[row][col] = 0
        game.current_board = json.dumps(current_grid)
        db.session.commit()
        return jsonify({'correct': True, 'erased': True, 'won': False})
        
    # 3. Check for invalid attempt (obvious duplicate in row, col, or box among already placed cells)
    temp_grid = [list(r) for r in current_grid]
    temp_grid[row][col] = 0 # Temporarily clear cell to validate the new value
    temp_board = Board.from_rows(temp_grid)
    
    if not temp_board.is_valid_move(row, col, value):
        # Rule violation (duplicate in group) -> Increment invalid attempts, block placement
        game.invalid_attempts += 1
        db.session.commit()
        return jsonify({
            'correct': False, 
            'invalid': True, 
            'invalid_attempts': game.invalid_attempts
        })
        
    # 4. Place valid move (even if it's incorrect against the solution, it is enterable)
    current_grid[row][col] = value
    game.current_board = json.dumps(current_grid)
    
    # 5. Check correctness against final solution
    is_correct = (value == solution_grid[row][col])
    if not is_correct:
        game.mistakes += 1
    
    # 6. Check if won
    won = (current_grid == solution_grid)
    if won:
        # Game won! Update score and games_played
        now = datetime.utcnow()
        elapsed = int((now - game.started_at).total_seconds()) + game.accumulated_seconds
        
        filled_count = sum(1 for r in range(9) for c in range(9) if initial_grid[r][c] == 0)
        
        # Scale invalid attempts (-0.5 penalty per invalid attempt, rounded at completion)
        rounded_invalid = int(round(game.invalid_attempts * 0.5))
        
        result = GameResult(
            completed=True,
            elapsed_seconds=elapsed,
            mistakes=game.mistakes,
            hints_used=game.hints_used,
            invalid_attempts=rounded_invalid,
            filled_cells=filled_count
        )
        
        profile_obj = PlayerProfile(
            skill_score=current_user.profile.skill_score,
            current_difficulty=Difficulty[current_user.profile.current_difficulty],
            games_played=current_user.profile.games_played
        )
        
        # Calculate rating and rank before update
        rating_before = current_user.profile.skill_score
        rank_before = None
        if current_user.profile.games_played >= 2: # Will be >= 3 after this game is saved
            leaderboard_before = get_leaderboard()
            for entry in leaderboard_before:
                if entry['profile'].user_id == current_user.profile.user_id:
                    rank_before = entry['rank']
                    break
        
        updated = profile_obj.record_result(result)
        
        # Apply updates
        current_user.profile.skill_score = updated.skill_score
        current_user.profile.current_difficulty = updated.current_difficulty.name
        current_user.profile.games_played = updated.games_played
        
        game.status = 'won'
        game.completed_at = now
        db.session.commit() # Save updates to calculate ranks
        
        # Calculate rank after update
        leaderboard_after = get_leaderboard()
        rank_after = None
        for entry in leaderboard_after:
            if entry['profile'].user_id == current_user.profile.user_id:
                rank_after = entry['rank']
                break
                
        # Update last_seen_rank
        current_user.profile.last_seen_rank = rank_after
        db.session.commit()
        
        return jsonify({
            'won': True,
            'correct': True,
            'new_score': updated.skill_score,
            'game_id': game.id,
            'rating_before': rating_before,
            'rating_after': updated.skill_score,
            'rank_before': rank_before,
            'rank_after': rank_after
        })
        
    db.session.commit()
    # Correct means it was enterable (no obvious duplicates), won is false
    return jsonify({
        'correct': True,
        'won': False,
        'solution_match': is_correct
    })

@game_bp.route('/game/api/hint', methods=['POST'])
@login_required
def hint():
    game = Game.query.filter_by(user_id=current_user.id, status='active').first()
    if not game:
        return jsonify({'error': 'No active game found.'}), 404
        
    initial_grid = json.loads(game.initial_board)
    current_grid = json.loads(game.current_board)
    solution_grid = json.loads(game.solution)
    
    # Find the first cell that is empty (0)
    hint_cell = None
    for r in range(9):
        for c in range(9):
            if current_grid[r][c] == 0:
                hint_cell = (r, c)
                break
        if hint_cell:
            break
            
    if not hint_cell:
        # No empty cells left, check if there's any wrong cell and fill it?
        # Standard use_hint fills first empty cell
        return jsonify({'error': 'No empty cells available for hint.'}), 400
        
    r, c = hint_cell
    correct_value = solution_grid[r][c]
    
    current_grid[r][c] = correct_value
    game.current_board = json.dumps(current_grid)
    game.hints_used += 1
    
    # Check if won
    won = (current_grid == solution_grid)
    rating_before = current_user.profile.skill_score
    rating_after = rating_before
    rank_before = None
    rank_after = None
    
    if won:
        now = datetime.utcnow()
        elapsed = int((now - game.started_at).total_seconds()) + game.accumulated_seconds
        filled_count = sum(1 for row in range(9) for col in range(9) if initial_grid[row][col] == 0)
        rounded_invalid = int(round(game.invalid_attempts * 0.5))
        
        result = GameResult(
            completed=True,
            elapsed_seconds=elapsed,
            mistakes=game.mistakes,
            hints_used=game.hints_used,
            invalid_attempts=rounded_invalid,
            filled_cells=filled_count
        )
        
        profile_obj = PlayerProfile(
            skill_score=current_user.profile.skill_score,
            current_difficulty=Difficulty[current_user.profile.current_difficulty],
            games_played=current_user.profile.games_played
        )
        
        # Calculate rank before
        if current_user.profile.games_played >= 2:
            leaderboard_before = get_leaderboard()
            for entry in leaderboard_before:
                if entry['profile'].user_id == current_user.profile.user_id:
                    rank_before = entry['rank']
                    break
                    
        updated = profile_obj.record_result(result)
        
        # Apply updates
        current_user.profile.skill_score = updated.skill_score
        current_user.profile.current_difficulty = updated.current_difficulty.name
        current_user.profile.games_played = updated.games_played
        
        game.status = 'won'
        game.completed_at = now
        db.session.commit()
        
        rating_after = updated.skill_score
        
        # Calculate rank after
        leaderboard_after = get_leaderboard()
        for entry in leaderboard_after:
            if entry['profile'].user_id == current_user.profile.user_id:
                rank_after = entry['rank']
                break
                
        current_user.profile.last_seen_rank = rank_after
        
    db.session.commit()
    
    return jsonify({
        'success': True,
        'row': r,
        'col': c,
        'value': correct_value,
        'hints_used': game.hints_used,
        'won': won,
        'game_id': game.id,
        'rating_before': rating_before,
        'rating_after': rating_after,
        'rank_before': rank_before,
        'rank_after': rank_after
    })

@game_bp.route('/game/api/restart', methods=['POST'])
@login_required
def restart():
    """Resigns the active game (imposing incomplete penalty) and redirects to Victory page."""
    game = Game.query.filter_by(user_id=current_user.id, status='active').first()
    if not game:
        return redirect(url_for('main.home'))
        
    now = datetime.utcnow()
    elapsed = int((now - game.started_at).total_seconds()) + game.accumulated_seconds
    rounded_invalid = int(round(game.invalid_attempts * 0.5))
    
    # Calculate score drop using completed=False
    result = GameResult(
        completed=False,
        elapsed_seconds=elapsed,
        mistakes=game.mistakes,
        hints_used=game.hints_used,
        invalid_attempts=rounded_invalid,
        filled_cells=0
    )
    
    profile_obj = PlayerProfile(
        skill_score=current_user.profile.skill_score,
        current_difficulty=Difficulty[current_user.profile.current_difficulty],
        games_played=current_user.profile.games_played
    )
    
    rating_before = current_user.profile.skill_score
    rank_before = None
    if current_user.profile.games_played >= 3:
        leaderboard_before = get_leaderboard()
        for entry in leaderboard_before:
            if entry['profile'].user_id == current_user.profile.user_id:
                rank_before = entry['rank']
                break
                
    updated = profile_obj.record_result(result)
    
    # Apply score and difficulty updates (DO NOT update games_played as it wasn't completed)
    current_user.profile.skill_score = updated.skill_score
    current_user.profile.current_difficulty = updated.current_difficulty.name
    
    game.status = 'abandoned'
    game.completed_at = now
    db.session.commit()
    
    # Calculate rank after drop
    rank_after = None
    if current_user.profile.games_played >= 3:
        leaderboard_after = get_leaderboard()
        for entry in leaderboard_after:
            if entry['profile'].user_id == current_user.profile.user_id:
                rank_after = entry['rank']
                break
                
    current_user.profile.last_seen_rank = rank_after
    db.session.commit()
    
    return redirect(url_for('game.victory', game_id=game.id, 
                           rating_before=rating_before, rating_after=updated.skill_score,
                           rank_before=rank_before or '', rank_after=rank_after or ''))

@game_bp.route('/victory/<int:game_id>')
@login_required
def victory(game_id):
    game = Game.query.get_or_404(game_id)
    if game.user_id != current_user.id:
        return redirect(url_for('main.home'))
        
    rating_before = request.args.get('rating_before', type=int)
    rating_after = request.args.get('rating_after', type=int)
    rank_before = request.args.get('rank_before')
    rank_after = request.args.get('rank_after')
    
    # Parse ranks
    rank_before = int(rank_before) if rank_before else None
    rank_after = int(rank_after) if rank_after else None
    
    return render_template(
        'victory.html',
        game=game,
        rating_before=rating_before,
        rating_after=rating_after,
        rank_before=rank_before,
        rank_after=rank_after
    )

@game_bp.route('/game/api/heartbeat', methods=['POST'])
@login_required
def heartbeat():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request body.'}), 400
        
    elapsed_seconds = data.get('elapsed_seconds')
    if elapsed_seconds is None:
        return jsonify({'error': 'Missing elapsed_seconds.'}), 400
        
    game = Game.query.filter_by(user_id=current_user.id, status='active').first()
    if not game:
        return jsonify({'error': 'No active game found.'}), 404
        
    game.accumulated_seconds = elapsed_seconds
    game.started_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})
