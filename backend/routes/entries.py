from flask import Blueprint, request, jsonify, current_app
# SQLAlchemy references removed - using Supabase
from backend.services.initial_processing import process_text
from backend.services.embedding import generate_embedding
import os
from supabase import create_client, Client
from functools import wraps

entries_bp = Blueprint('entries', __name__, url_prefix='/entries')

# Initialize Supabase client
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
)

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
            return f(user.user, *args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Token verification error!'}), 401
    
    return decorated

# Update all your route decorators from @token_required to @supabase_auth_required
@entries_bp.route('/entries', methods=['GET'])
@supabase_auth_required
def get_entries(current_user):
    """Get all entries for the current user"""
    try:
        response = supabase.table('entries').select('*').eq('user_id', current_user.id).order('created_at', desc=True).execute()
        all_entries = response.data
        return jsonify(all_entries), 200
    except Exception as e:
        print(f"Error getting entries: {str(e)}")
        return jsonify({'message': f'Error getting entries: {str(e)}'}), 500

@entries_bp.route('/entries', methods=['POST'])
@supabase_auth_required
def create_entry(current_user):
    """Create a new entry with processed content and immediate embedding"""
    print("Received request:", request.get_json())  # Debug print
    data = request.get_json()
    
    if not data or not data.get('content'):
        print("Invalid data received")  # Debug print
        return jsonify({'message': 'Content is required'}), 400
    
    try:
        # Process content through OpenAI
        print(f"Starting text processing for content: {data['content'][:100]}...")
        processed_content = process_text(data['content'])
        print(f"Text processing result: {processed_content}")
        
        if not processed_content:
            print("WARNING: Text processing failed - processed_content is None")
            processed_content = data['content']  # Fallback to original content
        
        # Get the next user entry ID
        user_entries_response = supabase.table('entries').select('user_entry_id').eq('user_id', current_user.id).execute()
        user_entry_count = len(user_entries_response.data)
        next_user_entry_id = user_entry_count + 1
        
        # Prepare entry data
        entry_data = {
            'user_id': current_user.id,
            'user_entry_id': next_user_entry_id,
            'content': data['content'],
            'processed': processed_content
        }
        
        # Generate embedding immediately for real-time search
        print(f"Starting embedding generation for processed content...")
        if processed_content:
            embedding = generate_embedding(processed_content)
            if embedding:
                entry_data['vectors'] = embedding
                print(f"✓ Generated embedding for new entry (length: {len(embedding)})")
            else:
                print(f"✗ Failed to generate embedding for new entry")
        else:
            print(f"✗ Skipping embedding generation - no processed content")
        
        # Create new entry in Supabase
        response = supabase.table('entries').insert(entry_data).execute()
        new_entry = response.data[0] if response.data else None
        
        if not new_entry:
            return jsonify({'message': 'Failed to create entry'}), 500
        
        # Uncomment if you want to add personality or story generation
        # personality = create_personality_and_write_to_db(new_entry['entry_id'], processed_content)        
        # new_entry['personality'] = personality
        
        # story = write_story_and_write_to_db(new_entry['entry_id'], processed_content)
        # new_entry['story'] = story
        
        return jsonify(new_entry), 201
    except Exception as e:
        print(f"Error creating entry: {str(e)}")
        return jsonify({'message': f'Error creating entry: {str(e)}'}), 500

@entries_bp.route('/entries/<int:entry_id>', methods=['GET'])
@supabase_auth_required
def get_entry(current_user, entry_id):
    """Get a specific entry by ID"""
    try:
        response = supabase.table('entries').select('*').eq('entry_id', entry_id).eq('user_id', current_user.id).execute()
        entry = response.data[0] if response.data else None
        
        if not entry:
            return jsonify({'message': 'Entry not found'}), 404
        
        return jsonify(entry), 200
    except Exception as e:
        print(f"Error getting entry: {str(e)}")
        return jsonify({'message': f'Error getting entry: {str(e)}'}), 500

@entries_bp.route('/entries/<int:entry_id>', methods=['PUT'])
@supabase_auth_required
def update_entry(current_user, entry_id):
    """Update an existing entry"""
    try:
        # Check if entry exists and belongs to user
        response = supabase.table('entries').select('*').eq('entry_id', entry_id).eq('user_id', current_user.id).execute()
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
        response = supabase.table('entries').update(update_data).eq('entry_id', entry_id).eq('user_id', current_user.id).execute()
        updated_entry = response.data[0] if response.data else None
        
        if not updated_entry:
            return jsonify({'message': 'Failed to update entry'}), 500
        
        return jsonify(updated_entry), 200
    except Exception as e:
        print(f"Error updating entry: {str(e)}")
        return jsonify({'message': f'Error updating entry: {str(e)}'}), 500

@entries_bp.route('/entries/<int:entry_id>', methods=['DELETE'])
@supabase_auth_required
def delete_entry(current_user, entry_id):
    """Delete an entry"""
    try:
        # Check if entry exists and belongs to user
        response = supabase.table('entries').select('*').eq('entry_id', entry_id).eq('user_id', current_user.id).execute()
        entry = response.data[0] if response.data else None
        
        if not entry:
            return jsonify({'message': 'Entry not found'}), 404
        
        # Delete entry from Supabase
        response = supabase.table('entries').delete().eq('entry_id', entry_id).eq('user_id', current_user.id).execute()
        
        return jsonify({'message': 'Entry deleted successfully'}), 200
    except Exception as e:
        print(f"Error deleting entry: {str(e)}")
        return jsonify({'message': f'Error deleting entry: {str(e)}'}), 500

@entries_bp.route('/entries/search', methods=['POST'])
@supabase_auth_required
def search_entries(current_user):
    """Search for similar entries using vector embeddings"""
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        from backend.services.embedding import search_by_text
        
        limit = data.get('limit', 5)
        # Only search the current user's entries
        similar_entries = search_by_text(data['query'], limit, user_id=current_user.id)
        
        return jsonify({
            'results': similar_entries
        }), 200
    except Exception as e:
        print(f"Error searching entries: {str(e)}")
        return jsonify({'error': str(e)}), 500 