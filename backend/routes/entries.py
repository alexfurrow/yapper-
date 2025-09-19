from flask import Blueprint, request, jsonify, current_app, g
from werkzeug.exceptions import InternalServerError
# SQLAlchemy references removed - using Supabase
from backend.services.initial_processing import process_text
from backend.services.embedding import generate_embedding
import os
from supabase import create_client, Client
from functools import wraps
from backend.config.logging import get_logger

# Set up logging
logger = get_logger(__name__)

# Required environment variables
REQUIRED_ENV = [
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
]

def validate_env():
    """Validate that all required environment variables are present"""
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        # Log only the variable names, not values
        raise InternalServerError(f"Missing required environment variables: {', '.join(missing)}")

entries_bp = Blueprint('entries', __name__, url_prefix='/entries')

# Validate environment variables
validate_env()

# Initialize Supabase client for service operations
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
)

# Function to create user-specific Supabase client
def create_user_supabase_client(user_token: str):
    """Create a Supabase client that operates as the authenticated user"""
    client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_ANON_KEY"]
    )
    # v2 way: attach JWT to PostgREST
    client.postgrest.auth(user_token)
    return client

# New Supabase auth decorator
def supabase_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'message': 'Token is missing!'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            # Verify token with Supabase
            user = supabase.auth.get_user(token)
            if not user.user:
                return jsonify({'message': 'Invalid token!'}), 401
            
            # Create user-specific Supabase client
            user_supabase = create_user_supabase_client(token)
            
            # Store in Flask g for global access
            g.current_user = user.user
            g.user_supabase = user_supabase
            
            # Call the function with original args (no extra arguments)
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Token verification error!'}), 401
    
    return decorated

# Update all your route decorators from @token_required to @supabase_auth_required
@entries_bp.route('/entries', methods=['GET'])
@supabase_auth_required
def get_entries():
    """Get all entries for the current user"""
    try:
        logger.info("Fetching entries", extra={"route": "/entries", "method": "GET", "user_id": g.current_user.id})
        response = g.user_supabase.table('entries').select('*').order('created_at', desc=True).execute()
        all_entries = response.data
        logger.info("Entries fetched successfully", extra={"route": "/entries", "method": "GET", "count": len(all_entries)})
        return jsonify(all_entries), 200
    except Exception as e:
        logger.exception("Error getting entries", extra={"route": "/entries", "method": "GET"})
        return jsonify({'message': f'Error getting entries: {str(e)}'}), 500

@entries_bp.route('/entries', methods=['POST'])
@supabase_auth_required
def create_entry():
    """Create a new entry with processed content and immediate embedding"""
    data = request.get_json()
    
    if not data or not data.get('content'):
        logger.warning("Create entry request missing content", extra={"route": "/entries", "method": "POST", "user_id": g.current_user.id})
        return jsonify({'message': 'Content is required'}), 400
    
    try:
        logger.info("Creating entry", extra={"route": "/entries", "method": "POST", "user_id": g.current_user.id, "content_length": len(data['content'])})
        
        # Process content through OpenAI
        processed_content = process_text(data['content'])
        
        # Get the next user entry ID using user context
        user_entries_response = g.user_supabase.table('entries').select('user_entry_id').execute()
        user_entry_count = len(user_entries_response.data)
        next_user_entry_id = user_entry_count + 1
        
        # Prepare entry data (don't include user_id - let RLS handle it)
        entry_data = {
            'user_entry_id': next_user_entry_id,
            'content': data['content'],
            'processed': processed_content
        }
        
        # Generate embedding immediately for real-time search
        if processed_content:
            embedding = generate_embedding(processed_content)
            if embedding:
                entry_data['vectors'] = embedding
                logger.info("Embedding generated for entry", extra={"route": "/entries", "method": "POST", "user_entry_id": next_user_entry_id})
        
        # Create new entry in Supabase
        response = g.user_supabase.table('entries').insert(entry_data).execute()
        new_entry = response.data[0] if response.data else None
        
        if not new_entry:
            logger.error("Failed to create entry - no data returned", extra={"route": "/entries", "method": "POST", "user_id": g.current_user.id})
            return jsonify({'message': 'Failed to create entry'}), 500
        
        # Uncomment if you want to add personality or story generation
        # personality = create_personality_and_write_to_db(new_entry['entry_id'], processed_content)        
        # new_entry['personality'] = personality
        
        # story = write_story_and_write_to_db(new_entry['entry_id'], processed_content)
        # new_entry['story'] = story
        
        logger.info("Entry created successfully", extra={"route": "/entries", "method": "POST", "user_id": g.current_user.id, "user_entry_id": next_user_entry_id})
        return jsonify(new_entry), 201
    except Exception as e:
        logger.exception("Error creating entry", extra={"route": "/entries", "method": "POST", "user_id": g.current_user.id})
        return jsonify({'message': f'Error creating entry: {str(e)}'}), 500

@entries_bp.route('/entries/<int:entry_id>', methods=['GET'])
@supabase_auth_required
def get_entry(entry_id):
    """Get a specific entry by ID"""
    try:
        response = g.user_supabase.table('entries').select('*').eq('user_entry_id', entry_id).execute()
        entry = response.data[0] if response.data else None
        
        if not entry:
            return jsonify({'message': 'Entry not found'}), 404
        
        return jsonify(entry), 200
    except Exception as e:
        logger.exception("Error getting entry", extra={"route": "/entries/<int:entry_id>", "method": "GET", "entry_id": entry_id})
        return jsonify({'message': f'Error getting entry: {str(e)}'}), 500

@entries_bp.route('/entries/<int:entry_id>', methods=['PUT'])
@supabase_auth_required
def update_entry(entry_id):
    """Update an existing entry"""
    try:
        # Check if entry exists and belongs to user
        response = g.user_supabase.table('entries').select('*').eq('user_entry_id', entry_id).execute()
        entry = response.data[0] if response.data else None
        
        if not entry:
            return jsonify({'message': 'Entry not found'}), 404
        
        data = request.get_json()
        
        if not data or not data.get('content'):
            return jsonify({'message': 'Content is required'}), 400
        
        # Prepare update data
        update_data = {'content': data['content']}
        
        # Re-process the content if requested
        if data.get('reprocess', False):
            processed_content = process_text(data['content'])
            update_data['processed'] = processed_content
            
        # Update entry in Supabase
        response = g.user_supabase.table('entries').update(update_data).eq('user_entry_id', entry_id).execute()
        updated_entry = response.data[0] if response.data else None
        
        if not updated_entry:
            return jsonify({'message': 'Failed to update entry'}), 500
        
        return jsonify(updated_entry), 200
    except Exception as e:
        logger.exception("Error updating entry", extra={"route": "/entries/<int:entry_id>", "method": "PUT", "entry_id": entry_id})
        return jsonify({'message': f'Error updating entry: {str(e)}'}), 500

@entries_bp.route('/entries/<int:entry_id>', methods=['DELETE'])
@supabase_auth_required
def delete_entry(entry_id):
    """Delete an entry"""
    try:
        # Check if entry exists and belongs to user
        response = g.user_supabase.table('entries').select('*').eq('user_entry_id', entry_id).execute()
        entry = response.data[0] if response.data else None
        
        if not entry:
            return jsonify({'message': 'Entry not found'}), 404
        
        # Delete entry from Supabase
        response = g.user_supabase.table('entries').delete().eq('user_entry_id', entry_id).execute()
        
        return jsonify({'message': 'Entry deleted successfully'}), 200
    except Exception as e:
        logger.exception("Error deleting entry", extra={"route": "/entries/<int:entry_id>", "method": "DELETE", "entry_id": entry_id})
        return jsonify({'message': f'Error deleting entry: {str(e)}'}), 500

@entries_bp.route('/entries/search', methods=['POST'])
@supabase_auth_required
def search_entries():
    """Search for similar entries using vector embeddings"""
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        from backend.services.embedding import search_by_text
        
        limit = data.get('limit', 5)
        # Only search the current user's entries
        similar_entries = search_by_text(data['query'], limit, user_id=g.current_user.id)
        
        return jsonify({
            'results': similar_entries
        }), 200
    except Exception as e:
        logger.exception("Error searching entries", extra={"route": "/entries/search", "method": "POST", "user_id": g.current_user.id})
        return jsonify({'error': str(e)}), 500