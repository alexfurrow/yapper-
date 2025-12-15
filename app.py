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
from backend.routes.chat import chat_bp
from backend.routes.converse import converse_bp
# from backend.routes.files import files_bp
from backend.routes.entries import entries_bp
from backend.routes.monthly_summaries import monthly_summaries_bp
from backend.commands import vectorize_pages_command, generate_monthly_summary_command, generate_all_monthly_summaries_command
from datetime import datetime
import pytz
# from backend.models.users import users


def create_app():
    app = Flask(__name__)
    
    # Configure logging
    import logging
    import sys
    # Set log level based on environment (DEBUG in dev, INFO/WARNING in prod)
    log_level = logging.DEBUG if os.environ.get('FLASK_DEBUG', 'False').lower() == 'true' else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)  # Explicitly output to stdout for Railway
        ]
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
    
    # Handle OPTIONS preflight requests BEFORE any route matching
    # This ensures CORS headers are set even if Flask's automatic OPTIONS handling fails
    @app.before_request
    def handle_options_preflight():
        if request.method == 'OPTIONS':
            origin = request.headers.get('Origin')
            log_msg = f"OPTIONS preflight: path={request.path}, origin={origin}, allowed={origin in allowed_origins if origin else False}"
            logger.info(log_msg)
            print(log_msg, flush=True)  # Backup print to stdout
            
            from flask import Response
            response = Response()
            response.status_code = 204  # No Content
            
            if origin and origin in allowed_origins:
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept, Origin'
                response.headers['Access-Control-Allow-Credentials'] = 'true'
                response.headers['Access-Control-Max-Age'] = '3600'
                logger.info(f"CORS headers set for origin: {origin}")
                print(f"CORS headers set for origin: {origin}", flush=True)
            else:
                logger.warning(f"Origin not allowed or missing: {origin}")
                print(f"WARNING: Origin not allowed or missing: {origin}", flush=True)
            
            logger.info(f"Response headers: {dict(response.headers)}")
            print(f"Response headers: {dict(response.headers)}", flush=True)
            return response

    # Add CORS headers to all responses (including OPTIONS preflight)
    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        
        if origin and origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept, Origin'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '3600'
            if request.method == 'OPTIONS':
                logger.info(f"after_request: Added CORS headers to OPTIONS response for {request.path}, origin: {origin}")
        elif origin:
            logger.warning(f"after_request: Origin not allowed: {origin} (path: {request.path}, method: {request.method})")
        
        return response

    # Register blueprints
    app.register_blueprint(entries_bp, url_prefix='/api/entries')
    app.register_blueprint(audio_bp, url_prefix='/api')
    app.register_blueprint(converse_bp, url_prefix='/api')
    app.register_blueprint(monthly_summaries_bp, url_prefix='/api/monthly-summaries')
    
    try:
        app.register_blueprint(chat_bp, url_prefix='/api')
    except Exception as e:
        # Log error but don't crash the app
        logger = logging.getLogger(__name__)
        logger.error(f"Error registering chat_bp: {str(e)}", exc_info=app.config['DEBUG'])
 
    # Register commands
    app.cli.add_command(vectorize_pages_command)
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
