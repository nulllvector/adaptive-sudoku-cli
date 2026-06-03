import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///sudoku.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
