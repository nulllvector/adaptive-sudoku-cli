from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    profile = db.relationship('Profile', backref='user', uselist=False, cascade="all, delete-orphan")
    settings = db.relationship('UserSettings', backref='user', uselist=False, cascade="all, delete-orphan")
    games = db.relationship('Game', backref='user', lazy=True, cascade="all, delete-orphan")

class Profile(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    skill_score = db.Column(db.Integer, nullable=False, default=0)
    current_difficulty = db.Column(db.String(20), nullable=False, default='BEGINNER')
    games_played = db.Column(db.Integer, nullable=False, default=0)
    difficulty_locked = db.Column(db.Boolean, nullable=False, default=False)
    last_seen_rank = db.Column(db.Integer, nullable=True)

class UserSettings(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    theme = db.Column(db.String(10), default='dark')
    show_timer = db.Column(db.Boolean, default=True)
    highlight_errors = db.Column(db.Boolean, default=True)
    highlight_related = db.Column(db.Boolean, default=True)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    initial_board = db.Column(db.Text, nullable=False) # JSON starting grid
    solution = db.Column(db.Text, nullable=False)      # JSON solution
    current_board = db.Column(db.Text, nullable=False)   # JSON current grid
    difficulty = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='active')  # 'active', 'won', 'abandoned'
    mistakes = db.Column(db.Integer, default=0)
    hints_used = db.Column(db.Integer, default=0)
    invalid_attempts = db.Column(db.Integer, default=0)
    accumulated_seconds = db.Column(db.Integer, default=0) # Persists elapsed time on exit
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
