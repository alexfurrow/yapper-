#Import crucial packages
import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Load environment
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, g
import uuid
from config import Config
from backend.routes.audio import audio_bp
from backend.routes.chat import chat_bp
from backend.routes.converse import converse_bp
# from backend.routes.files import files_bp
from backend.routes.entries import entries_bp
from backend.commands import vectorize_pages_command
from datetime import datetime
import pytz
# from backend.models.users import users


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure scheduler
    # app.config['SCHEDULER_API_ENABLED'] = True # Removed as per edit hint
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

    # Initialize extensions (SQLAlchemy removed - using Supabase)
    
    # Get Vercel URL from an environment variable for flexibility
    vercel_url = os.environ.get('FRONTEND_URL', None) # Example: Set FRONTEND_URL=https://my-yapper-frontend.vercel.app in Railway vars
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    if vercel_url:
        allowed_origins.append(vercel_url)
        # Optionally allow subdomains if needed (e.g., preview deployments)
        # allowed_origins.append(f"https://*.{vercel_url.split('//')[1]}") # Be careful with wildcards

    print(f"--- INFO: Allowed CORS Origins: {allowed_origins}") # Add for debugging
    print(f"--- INFO: FRONTEND_URL from env: {vercel_url}") # Add for debugging
    print(f"--- INFO: All environment variables containing 'FRONTEND': {[k for k in os.environ.keys() if 'FRONTEND' in k.upper()]}")
    print(f"--- INFO: All environment variables containing 'CORS': {[k for k in os.environ.keys() if 'CORS' in k.upper()]}")
    print(f"--- INFO: All environment variables containing 'ORIGIN': {[k for k in os.environ.keys() if 'ORIGIN' in k.upper()]}")

    # Add request ID middleware
    @app.before_request
    def add_request_id():
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    # Disable Flask-CORS to prevent conflicts with Railway
    # We'll use manual CORS headers instead
    print("--- INFO: Flask-CORS disabled, using manual CORS headers")
    
    # Add manual CORS headers to ensure they're set correctly
    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        print(f"--- DEBUG: Request origin: {origin}")
        print(f"--- DEBUG: Allowed origins: {allowed_origins}")
        
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            print(f"--- DEBUG: Set CORS origin to: {origin}")
        else:
            print(f"--- DEBUG: Origin {origin} not in allowed origins")
            
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept, Origin'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
        
        print(f"--- DEBUG: Final CORS headers: {dict(response.headers)}")
        return response
    
    # Handle preflight OPTIONS requests
    @app.route('/api/<path:path>', methods=['OPTIONS'])
    def handle_preflight(path):
        origin = request.headers.get('Origin')
        print(f"--- DEBUG: Preflight request for path: {path}")
        print(f"--- DEBUG: Preflight origin: {origin}")
        
        response = app.make_default_options_response()
        
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            print(f"--- DEBUG: Preflight CORS origin set to: {origin}")
        else:
            print(f"--- DEBUG: Preflight origin {origin} not allowed")
            
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept, Origin'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
        
        print(f"--- DEBUG: Preflight response headers: {dict(response.headers)}")
        return response
    # scheduler.init_app(app) # Removed as per edit hint

    # Register blueprints
    print("--- DEBUG: Registering blueprints...")
    app.register_blueprint(entries_bp, url_prefix='/api')
    print("  ✓ entries_bp registered with /api prefix")
    app.register_blueprint(audio_bp, url_prefix='/api')
    print("  ✓ audio_bp registered with /api prefix")
    app.register_blueprint(converse_bp, url_prefix='/api')
    print("  ✓ converse_bp registered with /api prefix")
    
    try:
        print(f"  Attempting to register chat_bp...")
        print(f"  chat_bp type: {type(chat_bp)}")
        print(f"  chat_bp name: {chat_bp.name}")
        print(f"  chat_bp url_prefix: {getattr(chat_bp, 'url_prefix', 'None')}")
        
        # Register chat blueprint without additional prefix since it already has /chat
        app.register_blueprint(chat_bp, url_prefix='/api')
        print("  ✓ chat_bp registered with /api prefix")
        
        # Check if routes were added
        print(f"  Routes after chat_bp registration:")
        for rule in app.url_map.iter_rules():
            if 'chat' in rule.endpoint:
                print(f"    {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
        
        # Also check all routes to see what's actually registered
        print(f"  All registered routes:")
        for rule in app.url_map.iter_rules():
            print(f"    {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
                
    except Exception as e:
        print(f"  ✗ ERROR registering chat_bp: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("--- DEBUG: Blueprint registration complete")
 
    # Register commands
    app.cli.add_command(vectorize_pages_command)

    return app

app = create_app()

with app.app_context():
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
    
    # Specifically check for chat routes
    print("\n--- DEBUG: Looking for chat routes ---")
    chat_routes = [rule for rule in app.url_map.iter_rules() if 'chat' in rule.endpoint]
    for rule in chat_routes:
        print(f"  Chat route: {rule.endpoint} -> {rule.rule} [{', '.join(rule.methods)}]")
    
    if not chat_routes:
        print("  WARNING: No chat routes found!")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
