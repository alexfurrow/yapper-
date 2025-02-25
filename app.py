from flask import Flask
from config import Config
from extensions import db, migrate, cors
from backend.routes.main import main_bp
from backend.routes.auth import auth_bp
from backend.routes.pages import pages_bp
from backend.routes.audio import audio_bp
# from backend.routes.personality import personality_bp
from backend.commands import vectorize_pages_command
from flask_apscheduler import APScheduler
from datetime import datetime
import pytz

scheduler = APScheduler()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure scheduler
    app.config['SCHEDULER_API_ENABLED'] = True
    
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
    scheduler.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(pages_bp, url_prefix='/api')
    app.register_blueprint(audio_bp, url_prefix='/api')
    # app.register_blueprint(personality_bp, url_prefix='/api')

    # Register commands
    app.cli.add_command(vectorize_pages_command)

    # Start the scheduler
    scheduler.start()

    return app

# Define the scheduled task
@scheduler.task('cron', id='vectorize_weekly', day_of_week='sun', hour=1, minute=0, 
               start_date='2025-03-02 01:00:00')
def scheduled_vectorize():
    with scheduler.app.app_context():
        from backend.services.embedding import vectorize_all_pages
        vectorize_all_pages()

# Add this scheduled task
@scheduler.task('cron', id='rebuild_index_weekly', day_of_week='mon', hour=2, minute=0, 
               start_date='2025-03-03 02:00:00')
def scheduled_index_rebuild():
    with scheduler.app.app_context():
        from backend.services.hnsw_index import build_and_save_index
        build_and_save_index()

app = create_app()

if __name__ == '__main__':
    app.run()
