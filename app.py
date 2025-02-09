from flask import Flask
from config import Config
from extensions import db, migrate, cors
from backend.routes.main import main_bp
from backend.routes.auth import auth_bp
from backend.routes.pages import pages_bp
from backend.routes.personality import personality_bp
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configure CORS to allow requests from React
    cors.init_app(app, resources={
        r"/*": {
            "origins": ["http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type"]
        }
    })

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(pages_bp, url_prefix='/api')
    app.register_blueprint(personality_bp, url_prefix='/api')

    return app

app = create_app()

if __name__ == '__main__':
    app.run()
