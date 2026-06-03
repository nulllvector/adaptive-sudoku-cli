from flask import Flask
from flask_login import LoginManager
from web.config import Config
from web.models import db, User

login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from web.auth import auth_bp
    from web.routes import main_bp
    from web.game_routes import game_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(game_bp)

    with app.app_context():
        db.create_all()

    return app
