from backend.config.environment import load_environment
load_environment()

import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from flask import Flask
from config import Config
from extensions import db, migrate, cors
from backend.routes.main import main_bp
from backend.routes.auth import auth_bp
from backend.routes.audio import audio_bp
from backend.routes.chat import chat_bp
# from backend.routes.files import files_bp
from backend.routes.entries import entries_bp
from backend.commands import vectorize_pages_command
from flask_apscheduler import APScheduler 
from datetime import datetime
import pytz
import os
from backend.models.users import users

scheduler = APScheduler()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure scheduler
    app.config['SCHEDULER_API_ENABLED'] = True
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configure CORS to allow requests from React
    cors.init_app(app, resources={
        r"/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    scheduler.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(entries_bp, url_prefix='/api')
    app.register_blueprint(audio_bp, url_prefix='/api')
    app.register_blueprint(chat_bp, url_prefix='/api')
 
    # Register commands
    app.cli.add_command(vectorize_pages_command)

    # Start the scheduler
    scheduler.start()

    # Database configuration
    if 'DATABASE_URL' not in os.environ:
        print("WARNING: DATABASE_URL environment variable not set!")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

    return app

# Define the scheduled task
@scheduler.task('cron', id='vectorize_weekly', day_of_week='sun', hour=1, minute=0, 
               start_date='2025-03-02 01:00:00')
def scheduled_vectorize():
    with scheduler.app.app_context():
        from backend.services.embedding import vectorize_all_entries
        vectorize_all_entries()

# Add this scheduled task
@scheduler.task('cron', id='rebuild_index_weekly', day_of_week='sun', hour=1, minute=30, 
               start_date='2025-03-03 02:00:00')
def scheduled_index_rebuild():
    with scheduler.app.app_context():
        from backend.services.hnsw_index import build_and_save_index
        build_and_save_index()

app = create_app()

with app.app_context():
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")

if __name__ == '__main__':
    app.run()
