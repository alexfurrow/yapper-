from flask import Flask
from config import Config
from extensions import db, migrate, cors
from backend.routes.main import main_bp
from backend.routes.auth import auth_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app

app = create_app()

if __name__ == '__main__':
    app.run()
