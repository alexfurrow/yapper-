#Import crucial packages
import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Load environment
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, g
import uuid
from backend.routes.audio import audio_bp
from backend.routes.audio_bulk import audio_bulk_bp
from backend.routes.chat import chat_bp
from backend.routes.converse import converse_bp
# from backend.routes.files import files_bp
from backend.routes.entries import entries_bp
from backend.routes.bulk_upload import bulk_upload_bp
from backend.routes.audit import audit_bp
from backend.commands import vectorize_pages_command
from backend.routes.monthly_summaries import monthly_summaries_bp
from backend.commands import vectorize_pages_command, generate_monthly_summary_command, generate_all_monthly_summaries_command
from datetime import datetime
import pytz
from flask_apscheduler import APScheduler
# from backend.models.users import users

# Initialize scheduler
scheduler = APScheduler()


def create_app():
    app = Flask(__name__)
    # Configuration now handled via environment variables (see below)

    # Configure scheduler
    app.config['SCHEDULER_API_ENABLED'] = True
    
    # Configure logging
    import logging
    # Set log level based on environment (DEBUG in dev, INFO/WARNING in prod)
    log_level = logging.DEBUG if os.environ.get('FLASK_DEBUG', 'False').lower() == 'true' else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration from environment variables
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
        
    # Configure allowed CORS origins
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://yapper-beta.vercel.app",
        "https://yapper.vercel.app"
    ]
    
    # Add URLs from environment variables (optional)
    frontend_url = os.environ.get('FRONTEND_URL', '').strip()
    if frontend_url:
        allowed_origins.extend([url.strip() for url in frontend_url.replace(',', ' ').split() if url.strip()])
    
    vercel_beta = os.environ.get('VERCEL_BETA_URL', '').strip()
    if vercel_beta:
        allowed_origins.append(vercel_beta)
    
    # Log allowed origins only in debug mode (security: don't expose in production)
    logger = logging.getLogger(__name__)
    logger.debug(f"Allowed CORS Origins: {allowed_origins}")

    # Add request ID middleware
    @app.before_request
    def add_request_id():
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))


    # Add manual CORS headers to ensure they're set correctly
    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
        # Don't set CORS headers for unauthorized origins (browser will reject)
            
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept, Origin, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
        
        return response
    
    # Handle preflight OPTIONS requests
    @app.route('/api/<path:path>', methods=['OPTIONS'])
    def handle_preflight(path):
        origin = request.headers.get('Origin')
        response = app.make_default_options_response()
        
        # Only set CORS headers for allowed origins
        if origin and origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept, Origin, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
        
        return response
    scheduler.init_app(app)

    # Register blueprints
    app.register_blueprint(entries_bp, url_prefix='/api/entries')
    app.register_blueprint(audio_bp, url_prefix='/api')
    print("  ✓ audio_bp registered with /api prefix")
    app.register_blueprint(audio_bulk_bp, url_prefix='/api')
    print("  ✓ audio_bulk_bp registered with /api prefix")
    app.register_blueprint(converse_bp, url_prefix='/api')
    print("  ✓ converse_bp registered with /api prefix")
    app.register_blueprint(bulk_upload_bp, url_prefix='/api')
    print("  ✓ bulk_upload_bp registered with /api prefix")
    app.register_blueprint(audit_bp, url_prefix='/api')
    print("  ✓ audit_bp registered with /api prefix")
    
    try:
        print(f"  Attempting to register chat_bp...")
        print(f"  chat_bp type: {type(chat_bp)}")
        print(f"  chat_bp name: {chat_bp.name}")
        print(f"  chat_bp url_prefix: {getattr(chat_bp, 'url_prefix', 'None')}")
        
        # Register chat blueprint without additional prefix since it already has /chat
    app.register_blueprint(monthly_summaries_bp, url_prefix='/api/monthly-summaries')
    
    try:
        app.register_blueprint(chat_bp, url_prefix='/api')
    except Exception as e:
        # Log error but don't crash the app
        logger = logging.getLogger(__name__)
        logger.error(f"Error registering chat_bp: {str(e)}", exc_info=app.config['DEBUG'])
 
    # Register commands
    app.cli.add_command(vectorize_pages_command)

    # Start the scheduler
    scheduler.start()

    # Database configuration removed - using Supabase directly
    app.cli.add_command(generate_monthly_summary_command)
    app.cli.add_command(generate_all_monthly_summaries_command)
    
    # Schedule monthly summary generation
    # Run on the 1st of each month at 2 AM
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        from backend.routes.monthly_summaries import generate_summaries_for_previous_month
        
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=generate_summaries_for_previous_month,
            trigger=CronTrigger(day=1, hour=2, minute=0),  # 1st of month at 2 AM
            id='generate_monthly_summaries',
            name='Generate monthly summaries for all users',
            replace_existing=True
        )
        scheduler.start()
        logger = logging.getLogger(__name__)
        logger.info("Monthly summary scheduler started (runs on 1st of each month at 2 AM)")
    except ImportError:
        logger = logging.getLogger(__name__)
        logger.warning("APScheduler not installed. Monthly summaries will not be automatically generated.")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error setting up scheduler: {str(e)}", exc_info=True)

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

# Scheduled task to permanently delete entries after 30 days
@scheduler.task('cron', id='permanently_delete_old_entries', day_of_week='sun', hour=2, minute=0,
               start_date='2025-01-15 02:00:00')
def scheduled_permanent_deletion():
    """Run weekly to permanently delete entries that have been soft-deleted for 30+ days"""
    with scheduler.app.app_context():
        from backend.services.entry_cleanup import permanently_delete_old_entries
        try:
            result = permanently_delete_old_entries()
            print(f"Scheduled permanent deletion completed: {result}")
        except Exception as e:
            print(f"Error in scheduled permanent deletion: {str(e)}")

app = create_app()

# Log registered routes in debug mode
import logging
logger = logging.getLogger(__name__)
if app.config['DEBUG']:
    with app.app_context():
        logger.debug("Registered routes:")
        for rule in app.url_map.iter_rules():
            logger.debug(f"  {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=app.config['DEBUG'])
