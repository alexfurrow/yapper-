###testing a commit
import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# --- ADD DEBUG HERE ---
print(f"--- DEBUG [app.py top level]: DATABASE_URL before load_environment: {os.environ.get('DATABASE_URL')}")
# --- END DEBUG ---

from backend.config.environment import load_environment
load_environment()

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
from datetime import datetime
import pytz
from backend.models.users import users


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure scheduler
    # app.config['SCHEDULER_API_ENABLED'] = True # Removed as per edit hint
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configure CORS to allow requests from React and Vercel
    # Get Vercel URL from an environment variable for flexibility
    vercel_url = os.environ.get('FRONTEND_URL', None) # Example: Set FRONTEND_URL=https://my-yapper-frontend.vercel.app in Railway vars
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    if vercel_url:
        allowed_origins.append(vercel_url)
        # Optionally allow subdomains if needed (e.g., preview deployments)
        # allowed_origins.append(f"https://*.{vercel_url.split('//')[1]}") # Be careful with wildcards

    print(f"--- INFO: Allowed CORS Origins: {allowed_origins}") # Add for debugging

    cors.init_app(app, resources={
        r"/api/*": { # Make sure CORS applies to your /api/* routes
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], # Add OPTIONS for preflight requests
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True # If you use cookies/sessions
        }
    })
    # scheduler.init_app(app) # Removed as per edit hint

    # Register blueprints
    print("--- DEBUG: Registering blueprints...")
    app.register_blueprint(main_bp)
    print("  ✓ main_bp registered")
    app.register_blueprint(auth_bp, url_prefix='/api')
    print("  ✓ auth_bp registered with /api prefix")
    app.register_blueprint(entries_bp, url_prefix='/api')
    print("  ✓ entries_bp registered with /api prefix")
    app.register_blueprint(audio_bp, url_prefix='/api')
    print("  ✓ audio_bp registered with /api prefix")
    
    try:
        app.register_blueprint(chat_bp, url_prefix='/api')
        print("  ✓ chat_bp registered with /api prefix")
    except Exception as e:
        print(f"  ✗ ERROR registering chat_bp: {str(e)}")
    
    print("--- DEBUG: Blueprint registration complete")
 
    # Register commands
    app.cli.add_command(vectorize_pages_command)

    # Start the scheduler
    # scheduler.start() # Removed as per edit hint

    # Database configuration
    db_url_from_env = os.environ.get('DATABASE_URL')
    print(f"--- DEBUG: DATABASE_URL from os.environ AFTER load_dotenv: {db_url_from_env}")
    if not db_url_from_env:
        print("CRITICAL WARNING: DATABASE_URL is not set in environment!")
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url_from_env
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Create tables if they don't exist
    with app.app_context():
        print(f"--- DEBUG: Attempting db.create_all() with URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        db.create_all()

    return app

# Define the scheduled task
# @scheduler.task('cron', id='vectorize_weekly', day_of_week='sun', hour=1, minute=0, 
#                start_date='2025-03-02 01:00:00')
# def scheduled_vectorize():
#     with scheduler.app.app_context():
#         from backend.services.embedding import vectorize_all_entries
#         vectorize_all_entries()

# Add this scheduled task
# @scheduler.task('cron', id='rebuild_index_weekly', day_of_week='sun', hour=1, minute=30, 
#                start_date='2025-03-03 02:00:00')
# def scheduled_index_rebuild():
#     with scheduler.app.app_context():
#         from backend.services.hnsw_index import build_and_save_index
#         build_and_save_index()

app = create_app()

with app.app_context():
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")

if __name__ == '__main__':
    app.run()
