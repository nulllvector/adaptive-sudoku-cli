import math
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from web.models import db, User, Profile, UserSettings, Game
from sudoku.difficulty import Difficulty

main_bp = Blueprint('main', __name__)

def calculate_sri(skill_score, games_played):
    return skill_score + (math.sqrt(games_played) * 2)

def get_leaderboard():
    """Returns a list of tuples: (rank, user, profile, sri) sorted by SRI desc."""
    profiles = Profile.query.filter(Profile.games_played >= 3).all()
    ranked_list = []
    for p in profiles:
        sri = calculate_sri(p.skill_score, p.games_played)
        ranked_list.append((p.user, p, sri))
        
    # Sort by SRI desc, break ties by username
    ranked_list.sort(key=lambda x: (x[2], x[0].username), reverse=True)
    
    leaderboard = []
    for index, (user, p, sri) in enumerate(ranked_list):
        leaderboard.append({
            'rank': index + 1,
            'user': user,
            'profile': p,
            'sri': sri,
            'tier': p.current_difficulty
        })
    return leaderboard


def check_rank_change(profile):
    """Checks if current user's rank changed and returns a notification message if so."""
    if profile.games_played < 3:
        if profile.last_seen_rank is not None:
            profile.last_seen_rank = None
            db.session.commit()
        return None

    leaderboard = get_leaderboard()
    current_rank = None
    for entry in leaderboard:
        if entry['profile'].user_id == profile.user_id:
            current_rank = entry['rank']
            break
            
    if current_rank is None:
        return None
        
    msg = None
    if profile.last_seen_rank is not None and profile.last_seen_rank != current_rank:
        diff = profile.last_seen_rank - current_rank
        if diff > 0:
            msg = f"While you were away, your leaderboard rank climbed from #{profile.last_seen_rank} to #{current_rank}!"
        else:
            msg = f"While you were away, your leaderboard rank dropped from #{profile.last_seen_rank} to #{current_rank}!"
            
    profile.last_seen_rank = current_rank
    db.session.commit()
    return msg

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return redirect(url_for('auth.login'))

@main_bp.route('/home')
@login_required
def home():
    # Check for offline rank change banner
    rank_alert = check_rank_change(current_user.profile)
    if rank_alert:
        flash(rank_alert, 'rank_alert')
        
    # Check if there is an active game
    active_game = Game.query.filter_by(user_id=current_user.id, status='active').first()
    
    # Calculate SRI if games >= 3
    sri = None
    if current_user.profile.games_played >= 3:
        sri = calculate_sri(current_user.profile.skill_score, current_user.profile.games_played)
        
    rating = current_user.profile.skill_score
    tier = current_user.profile.current_difficulty
        
    return render_template(
        'home.html', 
        profile=current_user.profile, 
        has_active_game=(active_game is not None),
        sri=sri,
        tier=tier
    )

@main_bp.route('/home/select-difficulty', methods=['POST'])
@login_required
def select_difficulty():
    if current_user.profile.difficulty_locked:
        flash('Difficulty is already locked. You must reset your account to change it.')
        return redirect(url_for('main.home'))
        
    diff_name = request.form.get('difficulty')
    if diff_name not in [d.name for d in Difficulty]:
        flash('Invalid difficulty selected.')
        return redirect(url_for('main.home'))
        
    diff = Difficulty[diff_name]
    # Rating mappings: BEGINNER: 0, EASY: 20, MEDIUM: 40, HARD: 60, EXPERT: 80
    score_mapping = {
        Difficulty.BEGINNER: 0,
        Difficulty.EASY: 20,
        Difficulty.MEDIUM: 40,
        Difficulty.HARD: 60,
        Difficulty.EXPERT: 80
    }
    
    current_user.profile.current_difficulty = diff_name
    current_user.profile.skill_score = score_mapping[diff]
    current_user.profile.difficulty_locked = True
    
    # Reset last_seen_rank as they are locking starting rating
    current_user.profile.last_seen_rank = None
    
    # Abandon all active games
    active_games = Game.query.filter_by(user_id=current_user.id, status='active').all()
    for g in active_games:
        g.status = 'abandoned'
        
    db.session.commit()
    flash(f"Starting difficulty set to {diff_name}. Your starting score is {current_user.profile.skill_score}.")
    return redirect(url_for('main.home'))

@main_bp.route('/home/reset', methods=['POST'])
@login_required
def reset():
    # Wipe profile back to initial onboarding state
    profile = current_user.profile
    profile.skill_score = 0
    profile.current_difficulty = 'BEGINNER'
    profile.games_played = 0
    profile.difficulty_locked = False
    profile.last_seen_rank = None
    
    # Abandon all active games
    active_games = Game.query.filter_by(user_id=current_user.id, status='active').all()
    for g in active_games:
        g.status = 'abandoned'
        
    db.session.commit()
    flash('Account reset successfully. Please select a starting difficulty.')
    return redirect(url_for('main.home'))

@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    settings_record = current_user.settings
    if request.method == 'POST':
        settings_record.theme = request.form.get('theme', 'dark')
        settings_record.show_timer = 'show_timer' in request.form
        settings_record.highlight_errors = 'highlight_errors' in request.form
        settings_record.highlight_related = 'highlight_related' in request.form
        
        db.session.commit()
        flash('Settings saved successfully.')
        return redirect(url_for('main.settings'))
        
    return render_template('settings.html', settings=settings_record)

@main_bp.route('/settings/delete-account', methods=['POST'])
@login_required
def delete_account():
    user = User.query.get(current_user.id)
    from flask_login import logout_user
    logout_user()
    db.session.delete(user)
    db.session.commit()
    flash('Your account and all associated data have been permanently deleted.')
    return redirect(url_for('auth.login'))

@main_bp.route('/leaderboard')
@login_required
def leaderboard():
    leaderboard_data = get_leaderboard()
    return render_template('leaderboard.html', leaderboard=leaderboard_data)
